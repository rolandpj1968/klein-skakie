import evaluate

class TTEntry:
    def __init__(self, lb_delta = -evaluate.Q_INFINITY_VAL, ub_delta = evaluate.Q_INFINITY_VAL, move = None):
        self.lb_delta = lb_delta
        self.ub_delta = ub_delta
        self.move = move
