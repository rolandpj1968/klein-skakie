import time

import chess

import evaluate
import tt

from util import fen4, move_list_to_sans
from move_sort import search_move_sort_key

# Engine config

# 0 means used fixed depth at MAX_DEPTH
DEFAULT_GAME_TIME_LIMIT_S = 0
GAME_TIME_LIMIT_S_KEY = "time-limit-s"

DEFAULT_MAX_DEPTH = 3
MAX_DEPTH_KEY = "max-depth"

# I believe MAX_QDEPTH should be even in order to be conservative - i.e. always allow the opponent to make the last capture
# With move ordering q-search does not explode, so this could be infinity...
DEFAULT_MAX_QDEPTH = 24
MAX_QDEPTH_KEY = "max-qdepth"

DEFAULT_DO_SEARCH_MOVE_SORT = True
DO_SEARCH_MOVE_SORT_KEY = "do-search-move-sort"

DEFAULT_DO_QSEARCH_MOVE_SORT = True
DO_QSEARCH_MOVE_SORT_KEY = "do-qsearch-move-sort"

# True iff we maintain and use a transition-table for quiescence search
DEFAULT_USE_QTT = False
USE_QTT_KEY = "use-qtt"

def config_val(config, key, default):
    val = default
    if key in config:
        val = config[key]
    return val

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
        self.n_depth_cut_nodes = [0] * (max_depth+1)
        self.n_depth_cut_siblings = [0] * (max_depth+1)

        self.n_qnodes = 0
        self.n_qpat_nodes = 0
        self.n_qcut_nodes = 0
        self.n_qdepth_nodes = [0] * (max_qdepth+1)

        self.n_qtt_hits = 0
        self.n_qtt_ub_hits = 0
        self.n_qtt_lb_hits = 0
        self.n_qtt_exact_hits = 0

class Engine:
    
    def __init__(self, board = chess.Board(), config = {}):
        # TODO - add position history from board
        self.board = board

        # engine config
        self.GAME_TIME_LIMIT_S = config_val(config, GAME_TIME_LIMIT_S_KEY, DEFAULT_GAME_TIME_LIMIT_S)
        self.MAX_DEPTH = config_val(config, MAX_DEPTH_KEY, DEFAULT_MAX_DEPTH)
        self.MAX_QDEPTH = config_val(config, MAX_QDEPTH_KEY, DEFAULT_MAX_QDEPTH)
        self.DO_SEARCH_MOVE_SORT = config_val(config, DO_SEARCH_MOVE_SORT_KEY, DEFAULT_DO_SEARCH_MOVE_SORT)
        self.DO_QSEARCH_MOVE_SORT = config_val(config, DO_QSEARCH_MOVE_SORT_KEY, DEFAULT_DO_QSEARCH_MOVE_SORT)
        self.USE_QTT = config_val(config, USE_QTT_KEY, DEFAULT_USE_QTT)
            
        # timing
        self.total_engine_time_s = 0
        
        self.fen4s = set()
        
        # TODO increments on each gen_move() - used to clear out TT and QTT of old cruft
        self.tt_epoch = 0
        
        # map: fen4 -> chess.Move
        self.tt = {}

        # map: fen4 -> tt.TTEntry
        self.qtt = {}
        
    def make_move(self, move):
        self.board.push(move)
        self.fen4s.add(fen4(self.board))

    def static_eval(self):
        return evaluate.static_eval(self.board)

    def iterative_deepening(self, move_time_limit_s):
        print("                                                               id time limit is %.3fs" % move_time_limit_s)
        max_depth = self.MAX_DEPTH
        if move_time_limit_s > 0:
            max_depth = 16
        id_start_time_s = time.time() 
        pv = []
        stats = None
        for depth_to_go in [n+1 for n in range(max_depth)]:
            stats = SearchStats(depth_to_go, self.MAX_QDEPTH)
            depth_start_time_s = time.time()
            # engine_move, val, rpv = self.alphabeta(stats, pv, 0, depth_to_go)
            engine_move, val, rpv = self.principal_variation_search(stats, pv, 0, depth_to_go)
            depth_end_time_s = time.time()
            depth_elapsed_time_s = depth_end_time_s - depth_start_time_s
            pv = rpv[::-1]
            move_san = self.board.san(engine_move)
            print("    depth %d %.3fs %s eval %d cp %s" % (depth_to_go, depth_elapsed_time_s, move_san, val, move_list_to_sans(self.board, pv)))
            print("                                        nodes %d wins %d draws %d leaves %d pvs %d cuts %d alls %d nodes by depth: %s" % (stats.n_nodes, stats.n_win_nodes, stats.n_draw_nodes, stats.n_leaf_nodes, stats.n_pv_nodes, stats.n_cut_nodes, stats.n_all_nodes, " ".join([str(n) for n in stats.n_depth_nodes])))
            print("                                        cut nodes nodes by depth: %s" % (" ".join(["%d/%d" % (stats.n_depth_cut_nodes[i], stats.n_depth_cut_siblings[i]) for i in range(len(stats.n_depth_cut_nodes))])))
            print("                                        qnodes %d qpats %d qtts %d qttubs %d qttlbs %d qttxs %d qcuts %d qnodes by depth %s" % (stats.n_qnodes, stats.n_qpat_nodes, stats.n_qtt_hits, stats.n_qtt_ub_hits, stats.n_qtt_lb_hits, stats.n_qtt_exact_hits, stats.n_qcut_nodes, " ".join([str(n) for n in stats.n_qdepth_nodes])))
            id_elapsed_time_s = depth_end_time_s - id_start_time_s
            print("                                                               id time limit is %.3fs - elapsed time is %.3fs" % (move_time_limit_s, id_elapsed_time_s))
            if move_time_limit_s > 0 and id_elapsed_time_s >= move_time_limit_s:
                break
        print()
        return engine_move, val, rpv, stats
        
    def quiesce_alphabeta(self, stats, depth_from_qroot, val, alpha = -evaluate.INFINITY_VAL, beta = evaluate.INFINITY_VAL, pos_fen4 = None):

        stats.n_qnodes += 1
        stats.n_qdepth_nodes[depth_from_qroot] += 1

        orig_alpha = alpha

        # If in check then stand pat is invalid and we consider all moves; not just captures/promos
        is_check = self.board.is_check()

        # print("                        %s %s val %d alpha %d beta %d check %s " % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check)), end='')

        best_eval = -evaluate.INFINITY_VAL
        best_move = None

        # Stand-pat
        if not is_check:
            best_eval = val
                
            if beta <= best_eval:
                stats.n_qpat_nodes += 1
                # print("                        %s %s val %d alpha %d beta %d check %s pat return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), val))
                return best_eval

            # Raise alpha to static eval cos we don't have to capture here
            if alpha < best_eval:
                alpha = best_eval
        
        if depth_from_qroot >= self.MAX_QDEPTH:
            # print("                        %s %s val %d alpha %d beta %d check %s MAX DEPTH return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), val))
            return val

        if self.USE_QTT:
            if pos_fen4 == None:
                pos_fen4 = fen4(self.board)
            
            if pos_fen4 in self.qtt:
                stats.n_qtt_hits += 1
                qtt_entry = self.qtt[pos_fen4]
                # print("qtt (%d, %d) " % (qtt_entry.lb, qtt_entry.ub), end='')
            else:
                qtt_entry = tt.TTEntry()
                self.qtt[pos_fen4] = qtt_entry

                # qtt_best_eval = None
                # qtt_best_move = None
        
            qtt_lb = qtt_entry.lb_delta + val
            qtt_ub = qtt_entry.ub_delta + val
            if qtt_ub <= orig_alpha:
                stats.n_qtt_ub_hits += 1
                # qtt_best_eval = qtt_ub
                # print("                        %s %s val %d alpha %d beta %d check %s  ub return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), qtt_ub))
                return qtt_ub

            elif beta <= qtt_lb:
                stats.n_qtt_lb_hits += 1
                # qtt_best_eval = qtt_lb
                # print("                        %s %s val %d alpha %d beta %d check %s  lb return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), qtt_lb))
                return qtt_lb

            elif qtt_lb == qtt_ub:
                stats.n_qtt_exact_hits += 1
                # qtt_best_eval = qtt_lb
                # print("                        %s %s val %d alpha %d beta %d check %s  exact return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), qtt_lb))
                return qtt_lb
            

        moves = list(self.board.legal_moves)
        
        # if there are no legal moves then this is checkmate or stalemate
        if not moves:
            if is_check:
                # relative to (static) val for QTT consistency
                best_eval = val - evaluate.CHECKMATE_VAL
            else:
                # relative to (static) val for QTT consistency - we really want 0 here but doesn't work with QTT and should be an edge case
                best_eval = val + evaluate.DRAW_VAL

            if self.USE_QTT:
                qtt_entry.lb_delta = best_eval - val
                qtt_entry.ub_delta = best_eval - val

            # print("                        %s %s val %d alpha %d beta %d check %s c/smate return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), best_eval))
            return best_eval

        if is_check:
            # evaluate all moves when in check
            qmoves = moves
        else:
            # ... otherwise just captures and promotions
            qmoves = [move for move in moves if self.board.is_capture(move) or move.promotion != None]

            if not qmoves:
                # no captures possible
                # print("                        %s %s val %d alpha %d beta %d check %s  no captures return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), val))
                return val
        
        if self.DO_QSEARCH_MOVE_SORT:
            qmoves.sort(key=lambda move: search_move_sort_key(self.board, move), reverse=True)

        move_no = 0
        for move in qmoves:

            promo_piece_val = 0
            if move.promotion != None:
                # replace a pawn with the promo piece
                promo_piece_val = evaluate.PIECE_VALS[chess.WHITE][move.promotion] - evaluate.PIECE_VALS[chess.WHITE][chess.PAWN]
            
            if self.board.is_capture(move):
                captured_piece_type = self.board.piece_type_at(move.to_square)
                if self.board.is_en_passant(move):
                    captured_piece_type = chess.PAWN
                static_move_val = val + evaluate.PIECE_VALS[chess.WHITE][captured_piece_type]
            else:
                static_move_val = val

            static_move_val += promo_piece_val

            move_eval = static_move_val
            if depth_from_qroot+1 < self.MAX_QDEPTH:
                self.board.push(move)
                move_eval = -self.quiesce_alphabeta(stats, depth_from_qroot+1, -static_move_val, -beta, -alpha)
                self.board.pop()
            else:
                stats.n_qdepth_nodes[self.MAX_QDEPTH] += 1

            if best_eval < move_eval:
                best_eval = move_eval
                best_move = move

                if beta <= move_eval:
                    break
                
            # if beta <= move_eval:
            #     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! bingo bongo bango !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            #     print("board fen %s orig_alpha %d beta %d val %d alpha %d best_eval %d move_eval %d move %s best_move %s" % (pos_fen4, orig_alpha, beta, val, alpha, best_eval, move_eval, str(move), str(best_move)))
            #     break

            if alpha < move_eval:
                alpha = move_eval

            move_no += 1

        # if qtt_best_eval != None and qtt_best_eval != best_eval:
        #     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! bingo bongo bango !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        #     print("board fen %s qt-entry (%d, %d, %s) -> qtt_best_eval %d orig_alpha %d beta %d val %d alpha %d best_eval %d best_move %s move_no %d qmoves %s" % (pos_fen4, qtt_entry.lb, qtt_entry.ub, str(qtt_entry.move), qtt_best_eval, orig_alpha, beta, val, alpha, best_eval, str(best_move), move_no, str(qmoves)))

        if self.USE_QTT:
            best_eval_delta = best_eval - val
            if best_eval <= orig_alpha:
                # All-node: we don't get a good idea of the best move
                node_type = "all"
                if best_eval_delta < qtt_entry.ub_delta:
                    qtt_entry.ub_delta = best_eval_delta

            else:
                if beta <= best_eval:
                    # Cut node
                    node_type = "cut"
                    stats.n_qcut_nodes += 1
                    if qtt_entry.lb_delta < best_eval_delta:
                        qtt_entry.move = best_move
                        qtt_entry.lb_delta = best_eval_delta

                else:
                    # Pv-node - this is an exact value
                    node_type = "pv"
                    qtt_entry.lb_delta = best_eval_delta
                    qtt_entry.ub_delta = best_eval_delta
                    qtt_entry.move = best_move

        # print("                        %s %s val %d alpha %d beta %d check %s %s return %d" % ("  " * depth_from_qroot, self.board.fen(), val, orig_alpha, beta, str(is_check), node_type, best_eval))
        return best_eval

    def alphabeta(self, stats, pv, depth_from_root, depth_to_go, alpha = -evaluate.INFINITY_VAL, beta = evaluate.INFINITY_VAL):
        stats.n_nodes += 1
        stats.n_depth_nodes[depth_from_root] += 1

        moves = list(self.board.legal_moves)
        
        # if there are no legal moves then this is checkmate or stalemate
        if not moves:
            if self.board.is_check():
                stats.n_win_nodes += 1
                # print("  %s AB %s alpha %d beta %d checkmate return %d" % ("  " * depth_from_root, self.board.fen(), alpha, beta, -evaluate.CHECKMATE_VAL))
                return None, -evaluate.CHECKMATE_VAL, []
            else:
                stats.n_draw_nodes += 1
                # print("  %s AB %s alpha %d beta %d stalemate return %d" % ("  " * depth_from_root, self.board.fen(), alpha, beta, evaluate.DRAW_VAL))
                return None, evaluate.DRAW_VAL, []
        
        pos_fen4 = fen4(self.board)
        
        if depth_from_root != 0 and pos_fen4 in self.fen4s:
            # TODO draw-rep nodes
            stats.n_draw_nodes += 1
            # print("  %s AB %s alpha %d beta %d repetition return %d" % ("  " * depth_from_root, self.board.fen(), alpha, beta, evaluate.DRAW_VAL))
            return None, evaluate.DRAW_VAL, []

        if depth_to_go == 0:
            stats.n_leaf_nodes += 1
            val = self.static_eval() * [-1, 1][self.board.turn]
            qval = self.quiesce_alphabeta(stats, 0, val, alpha, beta, pos_fen4)
            # print("  %s AB %s alpha %d beta %d quiesce return %d" % ("  " * depth_from_root, self.board.fen(), alpha, beta, qval))
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

        if self.DO_SEARCH_MOVE_SORT:
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
            stats.n_depth_cut_nodes[depth_from_root] += 1
            stats.n_depth_cut_siblings[depth_from_root] += move_no + 1
        elif orig_alpha < best_eval:
            stats.n_pv_nodes += 1
        else:
            stats.n_all_nodes += 1

        # Add move to TT if it's not an all node
        if orig_alpha < best_eval and move_no != 0:
            self.tt[pos_fen4] = best_move
            
        # print("  %s AB %s alpha %d beta %d recurse return %d" % ("  " * depth_from_root, self.board.fen(), orig_alpha, beta, best_eval))
        return best_move, best_eval, best_rpv
            
    def principal_variation_search(self, stats, pv, depth_from_root, depth_to_go, alpha = -evaluate.INFINITY_VAL, beta = evaluate.INFINITY_VAL):
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
            qval = self.quiesce_alphabeta(stats, 0, val, alpha, beta, pos_fen4)
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

        if self.DO_SEARCH_MOVE_SORT:
            moves.sort(key=lambda move: search_move_sort_key(self.board, move, pv_move, tt_move), reverse=True)

        move_no = 0
        for move in moves:
            if move == pv_move:
                child_pv = pv[1:]
            else:
                child_pv = []
                
            self.board.push(move)

            skip_nws = move_no == 0 or depth_to_go <= 2
            if skip_nws:
                probe_eval = alpha + 1
            else:
                # Null window search to see if this will raise alpha
                child_best_move, child_eval, child_rpv = self.principal_variation_search(stats, child_pv, depth_from_root+1, depth_to_go-1, -(alpha+1), -alpha)
                probe_eval = -child_eval

            if skip_nws or (alpha < probe_eval and probe_eval < beta):
                # Full window search - raise alpha since we can and our search is currently stable
                alpha = probe_eval - 1
                child_best_move, child_eval, child_rpv = self.principal_variation_search(stats, child_pv, depth_from_root+1, depth_to_go-1, -beta, -alpha)
                
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
            stats.n_depth_cut_nodes[depth_from_root] += 1
            stats.n_depth_cut_siblings[depth_from_root] += move_no + 1
        elif orig_alpha < best_eval:
            stats.n_pv_nodes += 1
        else:
            stats.n_all_nodes += 1

        # Add move to TT if it's not an all node
        if orig_alpha < best_eval and move_no != 0:
            self.tt[pos_fen4] = best_move
            
        return best_move, best_eval, best_rpv
            
    def gen_move(self):
        # TODO - implement epoch clearing...
        self.tt_epoch += 1
        self.tt.clear()
        self.qtt.clear()
        remaining_time_s = 0
        if self.GAME_TIME_LIMIT_S > 0:
            remaining_time_s = self.GAME_TIME_LIMIT_S - self.total_engine_time_s
        move_time_limit_s = remaining_time_s/48
        gen_move_start_s = time.time()
        engine_move, val, rpv, stats = self.iterative_deepening(move_time_limit_s)
        gen_move_end_s = time.time()
        gen_move_elapsed_time_s = gen_move_end_s - gen_move_start_s
        self.total_engine_time_s += gen_move_elapsed_time_s
        print("                                                   engine time so far %.3fs of %.3fs tt size is %d qtt size is %d" % (self.total_engine_time_s, self.GAME_TIME_LIMIT_S, len(self.tt), len(self.qtt)))
        pv = rpv[::-1]
        return engine_move, val, pv, stats
        
