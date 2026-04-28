from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import os
import re
import asyncio

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolCreate(BaseModel):
    service_id: str
    name: str
    description: Optional[str] = ""
    parameters_schema: Optional[dict] = {}
    code: Optional[str] = ""
    enabled: Optional[bool] = True


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters_schema: Optional[dict] = None
    code: Optional[str] = None
    enabled: Optional[bool] = None


def _type_map(json_type: str) -> str:
    return {"string": "str", "integer": "int", "number": "float",
            "boolean": "bool", "array": "list", "object": "dict"}.get(json_type, "str")


def generate_tool_function(name: str, description: str, schema: dict, body_code: str) -> str:
    """Generate a @mcp.tool() decorated async function from tool definition."""
    props = schema.get("properties", {})
    required = schema.get("required", [])

    params = []
    for param_name, param_schema in props.items():
        py_type = _type_map(param_schema.get("type", "string"))
        if param_name in required:
            params.append(f"{param_name}: {py_type}")
        else:
            params.append(f"{param_name}: Optional[{py_type}] = None")

    params_str = ", ".join(params)
    # Indent function body
    indented_body = "\n".join("    " + line for line in body_code.strip().splitlines())
    if not indented_body:
        indented_body = "    return {}"

    return f'''

@mcp.tool()
async def {name}({params_str}) -> dict:
    """{description}"""
{indented_body}
'''


def _get_service_port(address: str) -> Optional[int]:
    try:
        # e.g. http://127.0.0.1:5001 or http://127.0.0.1:5001/sse
        parts = address.rstrip("/").replace("/sse", "").split(":")
        return int(parts[-1])
    except Exception:
        return None


async def _restart_mcp_service(source_file: str, python_path: str, port: Optional[int]):
    """Kill the process on the service port and restart it."""
    # Kill existing process
    if port:
        try:
            proc = await asyncio.create_subprocess_shell(
                f"lsof -ti :{port} | xargs kill -9",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
        except Exception:
            pass
        await asyncio.sleep(1)

    # Determine python interpreter
    py = python_path.strip() if python_path and python_path.strip() else "python3"
    service_dir = os.path.dirname(os.path.abspath(source_file))
    service_file = os.path.basename(source_file)

    log_file = os.path.join(service_dir, "service.log")
    cmd = f"cd {service_dir} && nohup {py} {service_file} > {log_file} 2>&1 &"
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
    await asyncio.sleep(2)


@router.get("")
async def list_tools(service_id: str = None, search: str = None, enabled: bool = None):
    db = await get_db()
    query = "SELECT t.*, s.name as service_name FROM tools t LEFT JOIN services s ON t.service_id=s.id WHERE 1=1"
    params = []
    if service_id:
        query += " AND t.service_id=?"
        params.append(service_id)
    if search:
        query += " AND (t.name LIKE ? OR t.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if enabled is not None:
        query += " AND t.enabled=?"
        params.append(int(enabled))
    query += " ORDER BY s.name, t.name"
    rows = await db.execute(query, params)
    result = []
    async for r in rows:
        d = dict(r)
        d["parameters_schema"] = json.loads(d["parameters_schema"])
        result.append(d)
    await db.close()
    return result


@router.post("")
async def create_tool(data: ToolCreate):
    db = await get_db()
    row = await db.execute("SELECT id FROM services WHERE id=?", [data.service_id])
    svc = await row.fetchone()
    if not svc:
        await db.close()
        raise HTTPException(status_code=404, detail="Service not found")
    tool_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled, code) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [tool_id, data.service_id, data.name, data.description,
         json.dumps(data.parameters_schema), int(data.enabled), data.code or ""]
    )
    await db.execute(
        "UPDATE services SET tool_count = (SELECT COUNT(*) FROM tools WHERE service_id=?) WHERE id=?",
        [data.service_id, data.service_id]
    )
    await db.commit()
    await db.close()
    return {"id": tool_id, "message": "创建成功"}


@router.get("/{tool_id}")
async def get_tool(tool_id: str):
    db = await get_db()
    row = await db.execute(
        "SELECT t.*, s.name as service_name FROM tools t LEFT JOIN services s ON t.service_id=s.id WHERE t.id=?",
        [tool_id]
    )
    tool = await row.fetchone()
    if not tool:
        await db.close()
        raise HTTPException(status_code=404, detail="Tool not found")
    d = dict(tool)
    d["parameters_schema"] = json.loads(d["parameters_schema"])
    await db.close()
    return d


@router.put("/{tool_id}")
async def update_tool(tool_id: str, data: ToolUpdate):
    db = await get_db()
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        await db.close()
        return {"message": "no changes"}
    if "parameters_schema" in updates:
        updates["parameters_schema"] = json.dumps(updates["parameters_schema"])
    if "enabled" in updates:
        updates["enabled"] = int(updates["enabled"])
    set_clause = ", ".join(f"{k}=?" for k in updates)
    await db.execute(f"UPDATE tools SET {set_clause} WHERE id=?", list(updates.values()) + [tool_id])
    await db.commit()
    await db.close()
    return {"message": "更新成功"}


@router.patch("/{tool_id}")
async def toggle_tool(tool_id: str, data: dict):
    db = await get_db()
    if "enabled" in data:
        await db.execute("UPDATE tools SET enabled=? WHERE id=?", [int(data["enabled"]), tool_id])
        await db.commit()
    await db.close()
    return {"message": "ok"}


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str):
    db = await get_db()
    row = await db.execute("SELECT service_id FROM tools WHERE id=?", [tool_id])
    tool = await row.fetchone()
    if not tool:
        await db.close()
        raise HTTPException(status_code=404, detail="Tool not found")
    service_id = tool["service_id"]
    await db.execute("DELETE FROM tools WHERE id=?", [tool_id])
    await db.execute(
        "UPDATE services SET tool_count = (SELECT COUNT(*) FROM tools WHERE service_id=?) WHERE id=?",
        [service_id, service_id]
    )
    await db.commit()
    await db.close()
    return {"message": "删除成功"}


@router.post("/{tool_id}/deploy")
async def deploy_tool(tool_id: str):
    """Inject the tool's Python function into the MCP service source file and restart the service."""
    db = await get_db()
    row = await db.execute(
        """SELECT t.*, s.name as service_name, s.address, s.source_file, s.python_path
           FROM tools t LEFT JOIN services s ON t.service_id=s.id WHERE t.id=?""",
        [tool_id]
    )
    tool = await row.fetchone()
    await db.close()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool = dict(tool)

    if not tool.get("source_file"):
        raise HTTPException(
            status_code=400,
            detail="该微服务未配置源代码路径（source_file），请在服务管理中编辑并填写微服务的 main.py 路径"
        )

    source_file = tool["source_file"].strip()
    if not os.path.exists(source_file):
        raise HTTPException(status_code=400, detail=f"源文件不存在: {source_file}")

    if not tool.get("code", "").strip():
        raise HTTPException(
            status_code=400,
            detail="该工具没有函数代码，请先在编辑工具中填写函数体代码"
        )

    schema = json.loads(tool["parameters_schema"])
    new_code_block = generate_tool_function(
        tool["name"],
        tool.get("description", ""),
        schema,
        tool["code"]
    )

    # Read current source file
    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove existing definition of this tool if present
    pattern = (
        r'\n@mcp\.tool\(\)\nasync def '
        + re.escape(tool["name"])
        + r'\s*\([^)]*\)[^:]*:.*?(?=\n@mcp\.tool|\nif __name__|$)'
    )
    content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Insert new code block before if __name__ == "__main__":
    marker = 'if __name__ == "__main__":'
    if marker in content:
        content = content.replace(marker, new_code_block + marker)
    else:
        content += new_code_block

    # Write back
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(content)

    # Restart service
    port = _get_service_port(tool.get("address", ""))
    python_path = tool.get("python_path", "").strip()
    await _restart_mcp_service(source_file, python_path, port)

    # Re-sync tools from the service
    from backend.app.core.mcp_client import sync_tools
    tools_list = await sync_tools(tool.get("address", ""))
    if tools_list:
        db2 = await get_db()
        await db2.execute("DELETE FROM tools WHERE service_id=?", [tool["service_id"]])
        for t in tools_list:
            await db2.execute(
                "INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) VALUES (?,?,?,?,?,1)",
                [str(uuid.uuid4()), tool["service_id"], t["name"],
                 t.get("description", ""), json.dumps(t.get("inputSchema", {}))]
            )
        await db2.execute(
            "UPDATE services SET tool_count=?, status='online' WHERE id=?",
            [len(tools_list), tool["service_id"]]
        )
        await db2.commit()
        await db2.close()

    return {
        "message": f"工具 '{tool['name']}' 部署成功，微服务已重启并同步了 {len(tools_list)} 个工具",
        "tool_count": len(tools_list)
    }
