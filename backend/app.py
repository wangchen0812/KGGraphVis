from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase, basic_auth
from neo4j.graph import Node, Relationship, Path
import traceback
import os

# --- 配置 ---
app = Flask(__name__)
CORS(app)

# 【核心修改】从环境变量中读取Neo4j凭证
# os.environ.get('KEY', 'default_value') 的意思是：尝试读取名为'KEY'的环境变量，如果不存在，就使用后面的默认值。
# 在Zeabur上部署时，我们会设置这些环境变量，所以它会读取到。在本地运行时，如果没有设置，它会使用您写在代码里的默认值，不影响本地开发。
NEO4J_URI = os.environ.get('NEO4J_URI', "neo4j+s://f34a0b4d.databases.neo4j.io")
NEO4J_USER = os.environ.get('NEO4J_USER', "neo4j")
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', "JTYvsLt2quxhGvdp5JHHK2uQjEaQDg-yS9JgyNDJKFY")

# 检查是否成功获取密码，如果没有设置环境变量且没有默认值，则抛出错误
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD not found in environment variables")

driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

# --- 数据转换核心 ---
def sanitize_value(value):
    if isinstance(value, (str, int, float, bool, type(None))): return value
    if isinstance(value, list): return [sanitize_value(item) for item in value]
    if isinstance(value, dict): return {k: sanitize_value(v) for k, v in value.items()}
    return str(value)

def process_graph_result(records):
    nodes, links, node_ids = [], [], set()
    def add_node(node):
        node_id = str(node.element_id)
        if node_id not in node_ids:
            node_ids.add(node_id)
            node_props = dict(node)
            category = next(iter(node.labels), "未知") # 使用第一个标签作为类别
            name = node_props.get("Name") or node_props.get("name") or "未命名"
            nodes.append({"id": node_id, "name": str(name), "category": category, "properties": sanitize_value(node_props)})
    def add_link(rel):
        rel_props = dict(rel)
        rel_props['type'] = rel.type
        links.append({"source": str(rel.start_node.element_id), "target": str(rel.end_node.element_id), "name": rel.type, "properties": sanitize_value(rel_props)})

    for record in records:
        for value in record.values():
            if isinstance(value, Path):
                for node in value.nodes: add_node(node)
                for rel in value.relationships: add_link(rel)
            elif isinstance(value, Node): add_node(value)
            elif isinstance(value, Relationship):
                add_node(value.start_node); add_node(value.end_node); add_link(value)
    return {"nodes": nodes, "links": links}

def process_table_result(keys, records):
    headers = list(keys)
    rows = [dict(zip(headers, map(sanitize_value, record.values()))) for record in records]
    return {"headers": headers, "rows": rows}

# --- API 路由 ---
@app.route('/graph', methods=['POST'])
def get_graph_data():
    try:
        data = request.get_json()
        cypher_query = data.get('cypher', 'MATCH p=(n)-[r]->(m) RETURN p LIMIT 10')
        with driver.session() as session:
            result = session.run(cypher_query)
            keys = result.keys()
            records_list = list(result)

            # 智能判断返回类型
            is_graph = any(isinstance(value, (Node, Relationship, Path)) for record in records_list for value in record.values())

            if is_graph:
                response_data = process_graph_result(records_list)
                response_type = "graph"
            else:
                response_data = process_table_result(keys, records_list)
                response_type = "table"

            return jsonify({"type": response_type, "data": response_data})

    except Exception as e:
        print("="*20, " SERVER ERROR ", "="*20); traceback.print_exc(); print("="*50)
        return jsonify({"error": f"服务器内部错误: {type(e).__name__}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
