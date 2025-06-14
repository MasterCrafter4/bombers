from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys

from bombers import FireRescueModel, ScenarioParser, scenario_content

MODEL = None
FRAME_BUFFER = [] 
TURN_FRAME_COUNTER = 0 
INITIAL_STATE_SENT = False

def init_model():
    """Initialize simulation model"""
    global MODEL
    scenario = ScenarioParser.parse_scenario(scenario_content)
    MODEL = FireRescueModel(scenario)
    MODEL.json_exporter.save_frame = capture_frame
    return MODEL

def capture_frame(data):
    """Capture each frame generated during turn"""
    global FRAME_BUFFER, TURN_FRAME_COUNTER
    
    TURN_FRAME_COUNTER += 1
    data["frame"] = TURN_FRAME_COUNTER
    
    FRAME_BUFFER.append(data)
    return data

class Server(BaseHTTPRequestHandler):
    
    def do_POST(self):
        """Handle POST /step - only endpoint needed"""
        global MODEL, FRAME_BUFFER, TURN_FRAME_COUNTER, INITIAL_STATE_SENT
        
        if self.path == '/step':
            if MODEL is None:
                MODEL = init_model()
            
            if not INITIAL_STATE_SENT:
                initial_state = MODEL.json_exporter.initial_state(MODEL)
                initial_state["frame"] = 1
                initial_state["action"] = {"type": "initial_state", "message": "Initial game state"}
                
                response = {
                    "turn": 0,
                    "total_frames": 1,
                    "frames": [initial_state],
                    "summary": {
                        "rescued": 0, "lost": 0, "damage": 0,
                        "pois_active": len(MODEL.scenario["pois"])
                    }
                }
                
                INITIAL_STATE_SENT = True
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Continuar con el código existente
            if MODEL.simulation_over:
                response = {"message": "Simulation finished", "step": MODEL.step_count}
            else:
                FRAME_BUFFER = []
                TURN_FRAME_COUNTER = 0
                
                MODEL.step()
                
                action_frames = [frame for frame in FRAME_BUFFER 
                               if frame.get("action", {}).get("type") != "end_of_turn"]
                
                response = {
                    "turn": MODEL.step_count,
                    "total_frames": len(action_frames),
                    "frames": action_frames,
                    "summary": {
                        "rescued": MODEL.victims_rescued,
                        "lost": MODEL.victims_lost,
                        "damage": MODEL.damage_counters,
                        "pois_active": len(MODEL.scenario["pois"])
                    }
                } if action_frames else {
                    "turn": MODEL.step_count,
                    "total_frames": 0,
                    "frames": [],
                    "summary": {
                        "rescued": MODEL.victims_rescued,
                        "lost": MODEL.victims_lost,
                        "damage": MODEL.damage_counters,
                        "pois_active": len(MODEL.scenario["pois"])
                    }
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(port=8585):
    """Start server"""
    global INITIAL_STATE_SENT
    INITIAL_STATE_SENT = False  
    
    server = HTTPServer(('', port), Server)
    print(f"Server started on port {port}")
    print("Endpoint: POST /step")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("Server stopped")

if __name__ == '__main__':
    port = 8585
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run(port)