import json
import streamlit as st
import streamlit.components.v1 as components


def render_play_editor():
  st.markdown(
      "<h1 style='text-align: center; color: #F39C12;'>🎭 Custom Play Editor"
      "</h1>",
      unsafe_allow_html=True,
  )
  st.caption(
      "Drag blocks freely across the dark canvas to organize your play tree."
      " Connections update in real time!"
  )

  # -------------------------------------------------------------------------
  # 1. State Management
  # -------------------------------------------------------------------------
  if "nodes" not in st.session_state:
    st.session_state.nodes = {
        "scene_1": {
            "id": "scene_1",
            "title": "Scene 1: Balcony Decision",
            "video_url": "videos/genesis.mp4",
            "question": "Juliet offers her hand. What should Romeo do?",
        }
    }

  if "connections" not in st.session_state:
    st.session_state.connections = []

  if "edge_requirements" not in st.session_state:
    st.session_state.edge_requirements = {}

  # -------------------------------------------------------------------------
  # 2. Interactive Draggable Canvas (vis-network JS Integration)
  # -------------------------------------------------------------------------
  vis_nodes = []
  for n in st.session_state.nodes.values():
    label_text = f"🎬 {n['title']}\n📹 {n['video_url']}\n\"{n['question']}\""
    vis_nodes.append({
        "id": n["id"],
        "label": label_text,
        "shape": "box",
        "color": {
            "background": "#1E2228",
            "border": "#F39C12",
            "highlight": {"background": "#2D343F", "border": "#3498DB"},
        },
        "font": {"color": "#FFFFFF", "face": "Georgia", "size": 14},
        "margin": 15,
    })

  vis_edges = []
  for idx, conn in enumerate(st.session_state.connections):
    conn_key = f"{conn['from']}->{conn['to']}"
    req = st.session_state.edge_requirements.get(conn_key, "")
    vis_edges.append({
        "id": f"e_{idx}",
        "from": conn["from"],
        "to": conn["to"],
        "arrows": "to",
        "color": {"color": "#3498DB", "highlight": "#F39C12"},
        "width": 3,
        "label": req,
        "font": {"color": "#A0A0A0", "size": 12, "align": "top"},
    })

  nodes_json = json.dumps(vis_nodes)
  edges_json = json.dumps(vis_edges)

  canvas_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 480px;
                background-color: #121417;
                background-image: radial-gradient(#2A2E35 1px, transparent 1px);
                background-size: 20px 20px;
                border: 2px solid #333942;
                border-radius: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: new vis.DataSet({nodes_json}),
                edges: new vis.DataSet({edges_json})
            }};
            var options = {{
                physics: {{
                    enabled: false
                }},
                interaction: {{
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                }},
                edges: {{
                    smooth: {{
                        type: 'cubicBezier',
                        forceDirection: 'horizontal',
                        roundness: 0.4
                    }}
                }}
            }};
            var network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """

  components.html(canvas_code, height=500)

  st.markdown("---")

  # -------------------------------------------------------------------------
  # 3. Canvas Controls
  # -------------------------------------------------------------------------
  col_add, col_connect, col_req = st.columns([1, 1, 1.2])

  with col_add:
    st.subheader("➕ 1. Add Scene Block")
    scene_count = len(st.session_state.nodes) + 1
    new_title = st.text_input("Scene Title", value=f"Scene {scene_count}")
    new_url = st.text_input("Video Path/URL", value="videos/scene.mp4")
    new_q = st.text_input(
        "Question", value="What decision should Romeo make?"
    )

    if st.button("➕ Create Block", use_container_width=True):
      node_id = f"scene_{scene_count}"
      st.session_state.nodes[node_id] = {
          "id": node_id,
          "title": new_title,
          "video_url": new_url,
          "question": new_q,
      }
      st.rerun()

  with col_connect:
    st.subheader("🔗 2. Connect Blocks")
    node_keys = list(st.session_state.nodes.keys())

    if len(node_keys) < 2:
      st.info("Add at least 2 scene blocks to connect them.")
    else:
      src_node = st.selectbox("From Node:", node_keys, key="src_select")
      tgt_node = st.selectbox(
          "To Node:",
          [n for n in node_keys if n != src_node],
          key="tgt_select",
      )

      if st.button("🔗 Link Scenes", use_container_width=True):
        edge_exists = any(
            c["from"] == src_node and c["to"] == tgt_node
            for c in st.session_state.connections
        )
        if not edge_exists:
          st.session_state.connections.append(
              {"from": src_node, "to": tgt_node}
          )
          st.rerun()

  with col_req:
    st.subheader("⚙️ 3. Path Requirements")
    if not st.session_state.connections:
      st.info("No connected lines yet.")
    else:
      for conn in st.session_state.connections:
        s_name = st.session_state.nodes[conn["from"]]["title"]
        t_name = st.session_state.nodes[conn["to"]]["title"]
        conn_key = f"{conn['from']}->{conn['to']}"

        default_req = st.session_state.edge_requirements.get(
            conn_key, "e.g., Romeo should marry her"
        )
        user_req = st.text_input(
            f"[{s_name}] ➡️ [{t_name}]",
            value=default_req,
            key=f"input_{conn_key}",
        )
        st.session_state.edge_requirements[conn_key] = user_req

  # -------------------------------------------------------------------------
  # 4. JSON Blueprint Export
  # -------------------------------------------------------------------------
  with st.expander("📄 View Generated Play Blueprint (JSON)"):
    blueprint = {
        "nodes": st.session_state.nodes,
        "connections": [
            {
                "from": conn["from"],
                "to": conn["to"],
                "requirement": st.session_state.edge_requirements.get(
                    f"{conn['from']}->{conn['to']}", ""
                ),
            }
            for conn in st.session_state.connections
        ],
    }
    st.json(blueprint)


if __name__ == "__main__":
  st.set_page_config(page_title="The Bard's Play Editor", layout="wide")
  render_play_editor()