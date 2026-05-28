from matterlab_valves import RunzeSelectionValve

class RunzeValve:
    def __init__(self, com_port='COM12', address=0, num_port=16):
        self.valve = RunzeSelectionValve(com_port=com_port, address=address, num_port=num_port)

    def set_current_port(self, port):
        self.valve.set_current_port(port)
        print(f"Current port set to {port}")

    def get_current_port(self):
        port = self.valve.get_current_port()
        print(f"Current port is {port}")
    