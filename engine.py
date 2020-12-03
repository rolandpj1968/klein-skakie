import time
import chess

import evaluate

from util import fen4, move_list_to_sans
from move_sort import qsearch_move_sort_key, search_move_sort_key

MAX_DEPTH = 4
# I believe MAX_QDEPTH should be even in order to be conservative - i.e. always allow the opponent to make the last capture
MAX_QDEPTH = 24

DO_SEARCH_MOVE_SORT = True
DO_QSEARCH_MOVE_SORT = True

class SearchStats:
    def __init__(self, max_depth, max_qdepth):
        self.n_nodes = 0
        self.n_win_nodes = 0
        self.n_draw_nodes = 0
        self.n_leaf_nodes = 0
        self.n_pv_nodes = 0
        self.n_cut_nodes = 0
        self.n_all_nodes = 0
        self.n_depth_nodes = [0] * (max_depth+1)

        self.n_qnodes = 0
        self.n_qpat_nodes = 0
        self.n_qcut_nodes = 0
        self.n_qdepth_nodes = [0] * (max_qdepth+1)

class Engine:
    def __init__(self, board = chess.Board(), engine_time_allowed_s = 0):
        # TODO - add position history from board
        self.board = chess.Board()

        # timing
        self.engine_time_allowed_s = engine_time_allowed_s
        self.total_engine_time_s = 0
        
        self.fen4s = set()
        # increments on each gen_move() - used to clear out TT of old cruft
        self.tt_epoch = 0
        # map: fen4 -> chess.Move
        self.tt = {}

    def make_move(self, move):
        self.board.push(move)
        self.fen4s.add(fen4(self.board))

    def static_eval(self):
        return evaluate.static_eval(self.board)

    def iterative_deepening(self, time_limit_s):
        print("                                                               id time limit is %.3fs" % time_limit_s)
        max_depth = MAX_DEPTH
        if time_limit_s > 0:
            max_depth = 16
        id_start_time_s = time.time() 
        pv = []
        stats = None
        for depth_to_go in [n+1 for n in range(max_depth)]:
            stats = SearchStats(depth_to_go, MAX_QDEPTH)
            depth_start_time_s = time.time()
            engine_move, val, rpv = self.alphabeta(stats, pv, 0, depth_to_go)
            depth_end_time_s = time.time()
            depth_elapsed_time_s = depth_end_time_s - depth_start_time_s
            pv = rpv[::-1]
            move_san = self.board.san(engine_move)
            print("    depth %d %.3fs %s eval %d cp %s" % (depth_to_go, depth_elapsed_time_s, move_san, val, move_list_to_sans(self.board, pv)))
            print("                                        nodes %d wins %d draws %d leaves %d pvs %d cuts %d alls %d nodes by depth: %s" % (stats.n_nodes, stats.n_win_nodes, stats.n_draw_nodes, stats.n_leaf_nodes, stats.n_pv_nodes, stats.n_cut_nodes, stats.n_all_nodes, " ".join([str(n) for n in stats.n_depth_nodes])))
            print("                                        qnodes %d qpats %d qcuts %d qnodes by depth %s" % (stats.n_qnodes, stats.n_qpat_nodes, stats.n_qcut_nodes, " ".join([str(n) for n in stats.n_qdepth_nodes])))
            id_elapsed_time_s = depth_end_time_s - id_start_time_s
            print("                                                               id time limit is %.3fs - elapsed time is %.3fs" % (time_limit_s, id_elapsed_time_s))
            if time_limit_s > 0 and id_elapsed_time_s >= time_limit_s:
                break
        print()
        return engine_move, val, rpv, stats
        
    # return 
    def quiesce_alphabeta(self, stats, depth_from_qroot, val, alpha = -evaluate.INFINITY_VAL, beta = evaluate.INFINITY_VAL):

        stats.n_qnodes += 1
        stats.n_qdepth_nodes[depth_from_qroot] += 1

        # Stand pat - fail hard
        if beta <= val:
            stats.n_qpat_nodes += 1
            return beta
        
        if depth_from_qroot >= MAX_QDEPTH:
            return val
        
        best_eval = val

        moves = list(self.board.legal_moves)
        is_check = self.board.is_check()
        
        # if there are no legal moves then this is checkmate or stalemate
        if not moves:
            if is_check:
                return -evaluate.CHECKMATE_VAL
            else:
                return evaluate.DRAW_VAL

        if is_check:
            # evaluate all moves when in check
            qmoves = moves
        else:
            # ... otherwise just captures
            qmoves = [move for move in moves if self.board.is_capture(move)]
        
        if DO_QSEARCH_MOVE_SORT:
            qmoves.sort(key=lambda move: qsearch_move_sort_key(self.board, move, is_check), reverse=True)
                
        for move in qmoves:
            
            if is_check and not self.board.is_capture(move):
                static_move_val = val
            else:
                captured_piece_type = self.board.piece_type_at(move.to_square)
                if self.board.is_en_passant(move):
                    captured_piece_type = chess.PAWN
                static_move_val = val + evaluate.PIECE_VALS[chess.WHITE][captured_piece_type]

            # TODO take-backs at leaf
            move_eval = static_move_val
            if depth_from_qroot+1 < MAX_QDEPTH:
                self.board.push(move)
                move_eval = -self.quiesce_alphabeta(stats, depth_from_qroot+1, -static_move_val, -beta, -alpha)
                self.board.pop()
            else:
                stats.n_qdepth_nodes[MAX_QDEPTH] += 1

            # Fail hard in q-search
            if beta <= move_eval:
                stats.n_qcut_nodes += 1
                return beta

            if alpha < move_eval:
                alpha = move_eval
        
            if best_eval < move_eval:
                best_eval = move_eval
                    
        return best_eval

    def alphabeta(self, stats, pv, depth_from_root, depth_to_go, alpha = -evaluate.INFINITY_VAL, beta = evaluate.INFINITY_VAL):
        stats.n_nodes += 1
        stats.n_depth_nodes[depth_from_root] += 1

        moves = list(self.board.legal_moves)
        
        # if there are no legal moves then this is checkmate or stalemate
        if not moves:
            if self.board.is_check():
                stats.n_win_nodes += 1
                return None, -evaluate.CHECKMATE_VAL, []
            else:
                stats.n_draw_nodes += 1
                return None, evaluate.DRAW_VAL, []
        
        pos_fen4 = fen4(self.board)
        
        if depth_from_root != 0 and pos_fen4 in self.fen4s:
            # TODO draw-rep nodes
            stats.n_draw_nodes += 1
            return None, evaluate.DRAW_VAL, []

        if depth_to_go == 0:
            stats.n_leaf_nodes += 1
            val = self.static_eval() * [-1, 1][self.board.turn]
            qval = self.quiesce_alphabeta(stats, 0, val, alpha, beta)
            return None, qval, []

        if depth_from_root != 0:
            self.fen4s.add(pos_fen4)

        best_move = None
        best_eval = -evaluate.INFINITY_VAL
        best_rpv = []

        orig_alpha = alpha

        tt_move = None
        if pos_fen4 in self.tt:
            tt_move = self.tt[pos_fen4]
        
        pv_move = None
        child_pv = []
        if pv:
            pv_move = pv[0]

        if DO_SEARCH_MOVE_SORT:
            moves.sort(key=lambda move: search_move_sort_key(self.board, move, pv_move, tt_move), reverse=True)

        move_no = 0
        for move in moves:
            if move == pv_move:
                child_pv = pv[1:]
            else:
                child_pv = []
                
            self.board.push(move)
            child_best_move, child_eval, child_rpv = self.alphabeta(stats, child_pv, depth_from_root+1, depth_to_go-1, -beta, -alpha)
            self.board.pop()

            move_eval = -child_eval

            if best_eval < move_eval:
                best_move = move
                best_eval = move_eval
                
                if beta <= move_eval:
                    break
                
                child_rpv.append(move)
                best_rpv = child_rpv

            if alpha < move_eval:
                alpha = move_eval

            move_no += 1
        
        if depth_from_root != 0:
            self.fen4s.remove(pos_fen4)

        if beta <= best_eval:
            stats.n_cut_nodes += 1
        elif orig_alpha < best_eval:
            stats.n_pv_nodes += 1
        else:
            stats.n_all_nodes += 1

        # Add move to TT if it's not an all node
        if orig_alpha < best_eval and move_no != 0:
            self.tt[pos_fen4] = best_move
            
        return best_move, best_eval, best_rpv
            
    def gen_move(self):
        self.tt_epoch += 1
        self.tt.clear()
        remaining_time_s = 0
        if self.engine_time_allowed_s > 0:
            remaining_time_s = self.engine_time_allowed_s - self.total_engine_time_s
        gen_move_start_s = time.time()
        time_limit_s = remaining_time_s/48
        engine_move, val, rpv, stats = self.iterative_deepening(time_limit_s)
        gen_move_end_s = time.time()
        gen_move_elapsed_time_s = gen_move_end_s - gen_move_start_s
        self.total_engine_time_s += gen_move_elapsed_time_s
        print("                                                   engine time so far %.3fs of %.3fs tt size is %d" % (self.total_engine_time_s, self.engine_time_allowed_s, len(self.tt)))
        pv = rpv[::-1]
        return engine_move, val, pv, stats
        
