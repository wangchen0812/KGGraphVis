# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from neo4j import GraphDatabase, basic_auth
# from neo4j.graph import Node, Relationship, Path
# import traceback
# import os

# # --- 配置 ---
# app = Flask(__name__)
# # 【核心修正】为CORS配置添加根路径，并允许所有来源访问这个简单的健康检查点
# CORS(app, resources={
#     r"/graph": {"origins": "https://kg-graph-vis.vercel.app"},
#     r"/": {"origins": "*"}  # 允许任何人访问根路径
# })

# # 【核心修改】从环境变量中读取Neo4j凭证
# # os.environ.get('KEY', 'default_value') 的意思是：尝试读取名为'KEY'的环境变量，如果不存在，就使用后面的默认值。
# # 在Zeabur上部署时，我们会设置这些环境变量，所以它会读取到。在本地运行时，如果没有设置，它会使用您写在代码里的默认值，不影响本地开发。
# NEO4J_URI = os.environ.get('NEO4J_URI', "neo4j+s://f34a0b4d.databases.neo4j.io")
# NEO4J_USER = os.environ.get('NEO4J_USER', "neo4j")
# NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', "JTYvsLt2quxhGvdp5JHHK2uQjEaQDg-yS9JgyNDJKFY")

# # 检查是否成功获取密码，如果没有设置环境变量且没有默认值，则抛出错误
# if not NEO4J_PASSWORD:
#     raise ValueError("NEO4J_PASSWORD not found in environment variables")

# driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

# # --- 数据转换核心 ---
# def sanitize_value(value):
#     if isinstance(value, (str, int, float, bool, type(None))): return value
#     if isinstance(value, list): return [sanitize_value(item) for item in value]
#     if isinstance(value, dict): return {k: sanitize_value(v) for k, v in value.items()}
#     return str(value)

# def process_graph_result(records):
#     nodes, links, node_ids = [], [], set()
#     def add_node(node):
#         node_id = str(node.element_id)
#         if node_id not in node_ids:
#             node_ids.add(node_id)
#             node_props = dict(node)
#             category = next(iter(node.labels), "未知") # 使用第一个标签作为类别
#             name = node_props.get("Name") or node_props.get("name") or "未命名"
#             nodes.append({"id": node_id, "name": str(name), "category": category, "properties": sanitize_value(node_props)})
#     def add_link(rel):
#         rel_props = dict(rel)
#         rel_props['type'] = rel.type
#         links.append({"source": str(rel.start_node.element_id), "target": str(rel.end_node.element_id), "name": rel.type, "properties": sanitize_value(rel_props)})

#     for record in records:
#         for value in record.values():
#             if isinstance(value, Path):
#                 for node in value.nodes: add_node(node)
#                 for rel in value.relationships: add_link(rel)
#             elif isinstance(value, Node): add_node(value)
#             elif isinstance(value, Relationship):
#                 add_node(value.start_node); add_node(value.end_node); add_link(value)
#     return {"nodes": nodes, "links": links}

# def process_table_result(keys, records):
#     headers = list(keys)
#     rows = [dict(zip(headers, map(sanitize_value, record.values()))) for record in records]
#     return {"headers": headers, "rows": rows}

# # --- 【核心修正】添加一个新的健康检查路由 ---
# @app.route('/', methods=['GET'])
# def health_check():
#     """
#     这是一个健康检查端点。
#     当访问根URL时，返回一个JSON表示服务正在运行。
#     """
#     return jsonify({"status": "ok", "message": "Knowledge Graph API is running."})


# # --- API 路由 ---
# @app.route('/graph', methods=['POST'])
# def get_graph_data():
#     try:
#         data = request.get_json()
#         cypher_query = data.get('cypher', 'MATCH p=(n)-[r]->(m) RETURN p LIMIT 10')
#         with driver.session() as session:
#             result = session.run(cypher_query)
#             keys = result.keys()
#             records_list = list(result)

#             # 智能判断返回类型
#             is_graph = any(isinstance(value, (Node, Relationship, Path)) for record in records_list for value in record.values())

#             if is_graph:
#                 response_data = process_graph_result(records_list)
#                 response_type = "graph"
#             else:
#                 response_data = process_table_result(keys, records_list)
#                 response_type = "table"

#             return jsonify({"type": response_type, "data": response_data})

#     except Exception as e:
#         print("="*20, " SERVER ERROR ", "="*20); traceback.print_exc(); print("="*50)
#         return jsonify({"error": f"服务器内部错误: {type(e).__name__}"}), 500

# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


# backend/app.py

# 导入必要的库
from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase, basic_auth
import traceback
import os

# --- Flask应用配置 ---
app = Flask(__name__)

# 【核心修正】配置CORS (跨源资源共享)
# --------------------------------------------------------------------------
# 这是解决浏览器中“CORS policy”错误的关键。
# 我们在这里明确告诉后端服务器，允许来自指定前端域名的API请求。
# --------------------------------------------------------------------------

# 在这里填入您的Vercel前端部署后的域名
# 例如: "https://my-project-name.vercel.app"
YOUR_VERCEL_FRONTEND_URL = "https://my-kg-graph-vis.vercel.app" 

origins = [
    YOUR_VERCEL_FRONTEND_URL,
    # 如果您有自定义域名，也可以加在这里
    # "https://www.your-custom-domain.com", 
    # 为了方便本地开发测试，可以加上本地地址
    "http://localhost:5173",
]

# 对整个应用启用CORS，并指定允许的来源列表
CORS(app, origins=origins, supports_credentials=True)


# --- 数据库连接 ---
# --------------------------------------------------------------------------
# 从部署平台的环境变量中读取Neo4j数据库的连接凭证。
# --------------------------------------------------------------------------
NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

# 检查关键环境变量是否存在，如果缺少则在启动时就失败，并给出明确提示
if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise ValueError("Fatal Error: Missing one or more Neo4j environment variables (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)")

# 创建数据库驱动实例
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity() # 验证连接，如果无法连接，启动时会报错
except Exception as e:
    raise ConnectionError(f"Fatal Error: Could not connect to Neo4j database at {NEO4J_URI}. Error: {e}")


# --- 数据转换核心函数 ---
# --------------------------------------------------------------------------
# 这些函数负责将从Neo4j获取的数据，转换为前端ECharts可以识别的格式。
# --------------------------------------------------------------------------
def sanitize_value(value):
    """递归地清理数据，确保所有值都是JSON可序列化的。"""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    # 对于其他无法直接序列化的类型（如日期时间），转换为字符串
    return str(value)

def process_graph_result(records):
    """处理包含图结构（节点、关系、路径）的查询结果。"""
    nodes, links, node_ids = [], [], set()
    from neo4j.graph import Node, Relationship, Path

    def add_node(node):
        node_id = str(node.element_id)
        if node_id not in node_ids:
            node_ids.add(node_id)
            node_props = dict(node)
            category = next(iter(node.labels), "Unknown")
            name = node_props.get("Name") or node_props.get("name") or "Unnamed"
            nodes.append({"id": node_id, "name": str(name), "category": category, "properties": sanitize_value(node_props)})

    def add_link(rel):
        start_node_id = str(rel.start_node.element_id)
        end_node_id = str(rel.end_node.element_id)
        # 确保关系的两端节点都已被添加
        if start_node_id in node_ids and end_node_id in node_ids:
            rel_props = dict(rel)
            rel_props['type'] = rel.type
            links.append({"source": start_node_id, "target": end_node_id, "name": rel.type, "properties": sanitize_value(rel_props)})

    for record in records:
        for value in record.values():
            if isinstance(value, Path):
                for node in value.nodes: add_node(node)
                for rel in value.relationships: add_link(rel)
            elif isinstance(value, Node):
                add_node(value)
            elif isinstance(value, Relationship):
                add_node(value.start_node)
                add_node(value.end_node)
                add_link(value)
                
    return {"nodes": nodes, "links": links}

def process_table_result(keys, records):
    """处理表格形式的查询结果。"""
    headers = list(keys)
    rows = [dict(zip(headers, map(sanitize_value, record.values()))) for record in records]
    return {"headers": headers, "rows": rows}


# --- API 路由定义 ---
# --------------------------------------------------------------------------
# 定义后端对外提供服务的接口。
# --------------------------------------------------------------------------

@app.route('/', methods=['GET'])
def health_check():
    """
    健康检查端点。用于确认服务是否正在运行。
    直接在浏览器访问后端的根URL时，会看到这个返回结果。
    """
    return jsonify({"status": "ok", "message": "Knowledge Graph API is running."})


@app.route('/graph', methods=['POST'])
def get_graph_data():
    """
    处理前端发来的Cypher查询请求，并返回图数据或表格数据。
    """
    try:
        data = request.get_json()
        if not data or 'cypher' not in data:
            return jsonify({"error": "Bad Request: Missing 'cypher' in request body."}), 400
            
        cypher_query = data.get('cypher')

        with driver.session() as session:
            result = session.run(cypher_query)
            keys = result.keys()
            records_list = list(result)
            
            from neo4j.graph import Node, Relationship, Path
            is_graph = any(isinstance(value, (Node, Relationship, Path)) for record in records_list for value in record.values())
            
            if is_graph:
                response_data = process_graph_result(records_list)
                response_type = "graph"
            else:
                response_data = process_table_result(keys, records_list)
                response_type = "table"
                
            return jsonify({"type": response_type, "data": response_data})
            
    except Exception as e:
        # 在服务器日志中打印详细的错误信息，便于调试
        print("="*20, " SERVER ERROR ", "="*20)
        traceback.print_exc()
        print("="*50)
        # 返回给前端一个通用的、安全的错误信息
        return jsonify({"error": f"An internal server error occurred: {type(e).__name__}"}), 500

# --- 应用启动入口 ---
# --------------------------------------------------------------------------
# 这部分只在本地直接运行 `python app.py` 时执行。
# 在Koyeb上，Gunicorn会直接调用 `app` 对象，不会执行这里的代码。
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # 允许在本地通过 http://localhost:5001 访问
    app.run(debug=True, port=5001)

