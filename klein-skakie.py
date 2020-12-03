import sys
import chess

import cProfile

# From Sunfish
PIECE_VALS = (
    # BLACK
    (
        0, # nothing
        -100, # PAWN
        -280, # KNIGHT
        -320, # BISHOP
        -479, # ROOK
        -929, # QUEEN
        0, # KING
    ),
    (
        0, # nothing
        100, # PAWN
        280, # KNIGHT
        320, # BISHOP
        479, # ROOK
        929, # QUEEN
        0, # KING
    )
)

PIECE_POS_VALS = (
    # BLACK
    (
        # nothing
        (),
        # PAWN
        (   0,   0,   0,   0,   0,   0,   0,   0,
          -78, -83, -86, -73,-102, -82, -85, -90,
           -7, -29, -21, -44, -40, -31, -44,  -7,
           17, -16,   2, -15, -14,   0, -15,  13,
           26,  -3, -10,  -9,  -6,  -1,   0,  23,
           22,  -9,  -5,  11,  10,   2,  -3,  19,
           31,  -8,   7,  37,  36,  14,  -3,  31,
            0,   0,   0,   0,   0,   0,   0,   0),
        # KNIGHT
        (  66,  53,  75,  75,  10,  55,  58,  70,
            3,   6,-100,  36,  -4, -62,   4,  14,
          -10, -67,  -1, -74, -73, -27, -62,   2,
          -24, -24, -45, -37, -33, -41, -25, -17,
            1,  -5, -31, -21, -22, -35,  -2,   0,
           18, -10, -13, -22, -18, -15, -11,  14,
           23,  15,  -2,   0,  -2,   0,  23,  20,
           74,  23,  26,  24,  19,  35,  22,  69),
        # BISHOP
        (  59,  78,  82,  76,  23, 107,  37,  50,
           11, -20, -35,  42,  39, -31,  -2,  22,
            9, -39,  32, -41, -52,  10, -28,  14,
          -25, -17, -20, -34, -26, -25, -15, -10,
          -13, -10, -17, -23, -17, -16,   0,  -7,
          -14, -25, -24, -15,  -8, -25, -20, -15,
          -19, -20, -11,  -6,  -7,  -6, -20, -16,
            7,  -2,  15,  12,  14,  15,  10,  10),
        # ROOK
        ( -35, -29, -33,  -4, -37, -33, -56, -50,
          -55, -29, -56, -67, -55, -62, -34, -60,
          -19, -35, -28, -33, -45, -27, -25, -15,
            0,  -5, -16, -13, -18,   4,   9,   6,
           28,  35,  16,  21,  13,  29,  46,  30,
           42,  28,  42,  25,  25,  35,  26,  46,
           53,  38,  31,  26,  29,  43,  44,  53,
           30,  24,  18,  -5,   2,  18,  31,  32),
        # QUEEN
        (  -6,  -1,   8, 104, -69, -24, -88, -26,
          -14, -32, -60,  10, -20, -76, -57, -24,
            2, -43, -32, -60, -72, -63, -43,  -2,
           -1,  16, -22, -17, -25, -20,  13,   6,
           14,  15,   2,   5,   1,  10,  20,  22,
           30,   6,  13,  11,  16,  11,  16,  27,
           36,  18,   0,  19,  15,  15,  21,  38,
           39,  30,  31,  13,  31,  36,  34,  42),
        # KING
        (  -4, -54, -47,  99,  99, -60, -83,  62,
           32, -10, -55, -56, -56, -55, -10,  -3,
           62, -12,  57, -44,  67, -28, -37,  31,
           55, -50, -11,   4,  19, -13,   0,  49,
           55,  43,  52,  28,  51,  47,   8,  50,
           47,  42,  43,  79,  64,  32,  29,  32,
            4,  -3,  14,  50,  57,  18, -13,  -4,
          -17, -30,   3,  14,  -6,   1, -40, -18),
    ),
    # WHITE
    (
        # nothing
        (),
        # PAWN
        (   0,   0,   0,   0,   0,   0,   0,   0,
          -31,   8,  -7, -37, -36, -14,   3, -31,
          -22,   9,   5, -11, -10,  -2,   3, -19,
          -26,   3,  10,   9,   6,   1,   0, -23,
          -17,  16,  -2,  15,  14,   0,  15, -13,
            7,  29,  21,  44,  40,  31,  44,   7,
           78,  83,  86,  73, 102,  82,  85,  90,
            0,   0,   0,   0,   0,   0,   0,   0),
        # KNIGHT
        ( -74, -23, -26, -24, -19, -35, -22, -69,
          -23, -15,   2,   0,   2,   0, -23, -20,
          -18,  10,  13,  22,  18,  15,  11, -14,
           -1,   5,  31,  21,  22,  35,   2,   0,
           24,  24,  45,  37,  33,  41,  25,  17,
           10,  67,   1,  74,  73,  27,  62,  -2,
           -3,  -6, 100, -36,   4,  62,  -4, -14,
          -66, -53, -75, -75, -10, -55, -58, -70),
        # BISHOP
        (  -7,   2, -15, -12, -14, -15, -10, -10,
           19,  20,  11,   6,   7,   6,  20,  16,
           14,  25,  24,  15,   8,  25,  20,  15,
           13,  10,  17,  23,  17,  16,   0,   7,
           25,  17,  20,  34,  26,  25,  15,  10,
           -9,  39, -32,  41,  52, -10,  28, -14,
          -11,  20,  35, -42, -39,  31,   2, -22,
          -59, -78, -82, -76, -23,-107, -37, -50),
        # ROOK
        ( -30, -24, -18,   5,  -2, -18, -31, -32,
          -53, -38, -31, -26, -29, -43, -44, -53,
          -42, -28, -42, -25, -25, -35, -26, -46,
          -28, -35, -16, -21, -13, -29, -46, -30,
            0,   5,  16,  13,  18,  -4,  -9,  -6,
           19,  35,  28,  33,  45,  27,  25,  15,
           55,  29,  56,  67,  55,  62,  34,  60,
           35,  29,  33,   4,  37,  33,  56,  50),
        # QUEEN
        ( -39, -30, -31, -13, -31, -36, -34, -42,
          -36, -18,   0, -19, -15, -15, -21, -38,
          -30,  -6, -13, -11, -16, -11, -16, -27,
          -14, -15,  -2,  -5,  -1, -10, -20, -22,
            1, -16,  22,  17,  25,  20, -13,  -6,
           -2,  43,  32,  60,  72,  63,  43,   2,
           14,  32,  60, -10,  20,  76,  57,  24,
            6,   1,  -8,-104,  69,  24,  88,  26),
        # KING
        (  17,  30,  -3, -14,   6,  -1,  40,  18,
           -4,   3, -14, -50, -57, -18,  13,   4,
          -47, -42, -43, -79, -64, -32, -29, -32,
          -55, -43, -52, -28, -51, -47,  -8, -50,
          -55,  50,  11,  -4, -19,  13,   0, -49,
          -62,  12, -57,  44, -67,  28,  37, -31,
          -32,  10,  55,  56,  56,  55,  10,   3,
            4,  54,  47, -99, -99,  60,  83, -62),
    )
)

INFINITY_VAL = 1000000
CHECKMATE_VAL = 20000
DRAW_VAL = 0

MAX_DEPTH = 4
# I believe MAX_QDEPTH should be even in order to be conservative - i.e. always allow the opponent to make the last capture
MAX_QDEPTH = 24

DO_SEARCH_MOVE_SORT = True
DO_QSEARCH_MOVE_SORT = True

# Doesn't seem to help much over basic move ordering
DO_USE_ID_PV = True

# FEN representation of the board with the half-move and full-move counts removed
# Used for repeated position checks
def fen4(board):
    return " ".join(board.fen().split()[:4])

def move_list_to_sans(orig_board, moves):
    board = orig_board.copy()
    
    sans = []
    for move in moves:
        sans.append(board.san(move))
        board.push(move)

    return sans

# Greatest victim least attacker, else 0
def qsearch_move_sort_key(board, move, is_check):
    if is_check and not board.is_capture(move):
        return 0
    
    captured_piece_type = board.piece_type_at(move.to_square)
    if board.is_en_passant(move):
        captured_piece_type = chess.PAWN
    attacker_piece_type = board.piece_type_at(move.from_square)

    return (captured_piece_type << 4) - attacker_piece_type

SEARCH_MOVE_BASE = 1024*1024
SEARCH_MOVE_PV_MOVE = 5 * SEARCH_MOVE_BASE
SEARCH_MOVE_WINNING_CAPTURE_BASE = 4 * SEARCH_MOVE_BASE
SEARCH_MOVE_EVEN_CAPTURE_BASE = 3 * SEARCH_MOVE_BASE
SEARCH_MOVE_NON_LOSING_NON_CAPTURE_BASE = 2 * SEARCH_MOVE_BASE
SEARCH_MOVE_LOSING_CAPTURE_BASE = 1 * SEARCH_MOVE_BASE
SEARCH_MOVE_LOSING_NON_CAPTURE_BASE = 0 * SEARCH_MOVE_BASE

# For winning captures, greatest victim least attacker
#   then non-losing non-captures by least attacker
#   then even captures by greatest attacker
#   then losing captures, greatest victim least attacker
#   then losing non-captures by least attacker
# Break ties with piece-pos delta
def search_move_sort_key(board, move, pv_move):
    if DO_USE_ID_PV and move == pv_move:
        return SEARCH_MOVE_PV_MOVE

    moving_piece_type = board.piece_type_at(move.from_square)
    is_capture = board.is_capture(move)
    is_target_attacked = board.is_attacked_by(not board.turn, move.to_square)

    moving_piece_val = PIECE_VALS[chess.WHITE][moving_piece_type]
    moving_piece_pp = PIECE_POS_VALS[board.turn][moving_piece_type]
    pp_delta = (moving_piece_pp[move.to_square] - moving_piece_pp[move.from_square]) * [-1, 1][board.turn]

    if is_capture:
        captured_piece_type = board.piece_type_at(move.to_square)
        if board.is_en_passant(move):
            captured_piece_type = chess.PAWN

        captured_piece_val = PIECE_VALS[chess.WHITE][captured_piece_type]
        
        gvla = (captured_piece_val << 10) - moving_piece_val
        if is_target_attacked:
            
            if captured_piece_type > moving_piece_type:
                # Winning capture #1
                return SEARCH_MOVE_WINNING_CAPTURE_BASE + gvla + pp_delta
            
            if captured_piece_type == moving_piece_type:
                # Even capture
                return SEARCH_MOVE_EVEN_CAPTURE_BASE + captured_piece_val + pp_delta

            # Losing capture
            return SEARCH_MOVE_LOSING_CAPTURE_BASE + gvla + pp_delta

        else:
            # Winning captured #2 - clean capture 
            return SEARCH_MOVE_WINNING_CAPTURE_BASE + gvla + pp_delta

    else:
        # non-capture

        
        if is_target_attacked:
            return SEARCH_MOVE_LOSING_NON_CAPTURE_BASE - moving_piece_val + pp_delta
        else:
            return SEARCH_MOVE_NON_LOSING_NON_CAPTURE_BASE + pp_delta

    

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
    def __init__(self, board = chess.Board()):
        self.board = chess.Board()
        # TODO - add position history from board
        self.fen4s = set()

    def make_move(self, move):
        self.board.push(move)
        self.fen4s.add(fen4(self.board))

    def static_eval(self):
        val = 0
        for color in [chess.BLACK, chess.WHITE]:
            color_piece_vals = PIECE_VALS[color]
            color_piece_pos_vals = PIECE_POS_VALS[color]
            for piece_type in [chess.PAWN,  chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
                sqSet = self.board.pieces(piece_type, color)
                if sqSet != 0:
                    piece_val = color_piece_vals[piece_type]
                    piece_pos_vals = color_piece_pos_vals[piece_type]
                    while sqSet != 0:
                        sq = sqSet.pop()
                        val += piece_val
                        val += piece_pos_vals[sq]
        return val

    def iterative_deepening(self, stats):
        pv = []
        for depth_to_go in [n+1 for n in range(MAX_DEPTH)]:
            stats = SearchStats(depth_to_go, MAX_QDEPTH)
            # engine_move, val, rpv = self.minimax(stats, 0, MAX_DEPTH)
            engine_move, val, rpv = self.alphabeta(stats, pv, 0, depth_to_go, -INFINITY_VAL, INFINITY_VAL)
            pv = rpv[::-1]
            move_san = self.board.san(engine_move)
            print("    depth %d %s eval %d cp %s" % (depth_to_go, move_san, val, move_list_to_sans(self.board, pv)))
            print("                                        nodes %d wins %d draws %d leaves %d pvs %d cuts %d alls %d nodes by depth: %s" % (stats.n_nodes, stats.n_win_nodes, stats.n_draw_nodes, stats.n_leaf_nodes, stats.n_pv_nodes, stats.n_cut_nodes, stats.n_all_nodes, " ".join([str(n) for n in stats.n_depth_nodes])))
            print("                                        qnodes %d qpats %d qcuts %d qnodes by depth %s" % (stats.n_qnodes, stats.n_qpat_nodes, stats.n_qcut_nodes, " ".join([str(n) for n in stats.n_qdepth_nodes])))
        print()
        return engine_move, val, rpv
        
    def quiesce_minimax(self, stats, depth_from_qroot, val):
        
        stats.n_qnodes += 1
        stats.n_qdepth_nodes[depth_from_qroot] += 1

        if depth_from_qroot >= MAX_QDEPTH:
            return val
        
        best_eval = val
        
        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                captured_piece_type = self.board.piece_type_at(move.to_square)
                if self.board.is_en_passant(move):
                    captured_piece_type = chess.PAWN
                static_move_val = val + PIECE_VALS[chess.WHITE][captured_piece_type]

                # TODO take-back at leaf
                move_eval = static_move_val
                if depth_from_qroot+1 < MAX_QDEPTH:
                    self.board.push(move)
                    move_eval = -self.quiesce_minimax(stats, depth_from_qroot+1, -static_move_val)
                    self.board.pop()
                else:
                    stats.n_qdepth_nodes[MAX_QDEPTH] += 1

                if best_eval < move_eval:
                    best_eval = move_eval
                    
        return best_eval

    def minimax(self, stats, depth_from_root, depth_to_go):
        stats.n_nodes += 1
        stats.n_depth_nodes[depth_from_root] += 1
        
        if self.board.is_checkmate():
            stats.n_win_nodes += 1
            return None, -CHECKMATE_VAL + depth_from_root, []

        pos_fen4 = fen4(self.board)
        
        if self.board.is_stalemate() or (depth_from_root != 0 and pos_fen4 in self.fen4s):
            stats.n_draw_nodes += 1
            return None, DRAW_VAL, []
        
        if depth_to_go == 0:
            stats.n_leaf_nodes += 1
            val = self.static_eval() * [-1, 1][self.board.turn]
            qval = self.quiesce_minimax(stats, 0, val)
            return None, qval, []

        if depth_from_root != 0:
            self.fen4s.add(pos_fen4)

        best_move = None
        best_eval = -INFINITY_VAL
        best_rpv = []

        for move in self.board.legal_moves:
            self.board.push(move)
            child_best_move, child_eval, child_rpv = self.minimax(stats, depth_from_root+1, depth_to_go-1)
            self.board.pop()

            move_eval = -child_eval
        
            if best_eval < move_eval:
                best_move = move
                best_eval = move_eval
                child_rpv.append(self.board.san(move))
                best_rpv = child_rpv

        if depth_from_root != 0:
            self.fen4s.remove(pos_fen4)
            
        return best_move, best_eval, best_rpv

    # return 
    def quiesce_alphabeta(self, stats, depth_from_qroot, val, alpha, beta):

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
                return -CHECKMATE_VAL
            else:
                return DRAW_VAL

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
                static_move_val = val + PIECE_VALS[chess.WHITE][captured_piece_type]

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

    def alphabeta(self, stats, pv, depth_from_root, depth_to_go, alpha, beta):
        stats.n_nodes += 1
        stats.n_depth_nodes[depth_from_root] += 1

        moves = list(self.board.legal_moves)
        
        # if there are no legal moves then this is checkmate or stalemate
        if not moves:
            if self.board.is_check():
                stats.n_win_nodes += 1
                return None, -CHECKMATE_VAL, []
            else:
                stats.n_draw_nodes += 1
                return None, DRAW_VAL, []
        
        pos_fen4 = fen4(self.board)
        
        if depth_from_root != 0 and pos_fen4 in self.fen4s:
            # TODO draw-rep nodes
            stats.n_draw_nodes += 1
            return None, DRAW_VAL, []

        if depth_to_go == 0:
            stats.n_leaf_nodes += 1
            val = self.static_eval() * [-1, 1][self.board.turn]
            qval = self.quiesce_alphabeta(stats, 0, val, alpha, beta)
            return None, qval, []

        if depth_from_root != 0:
            self.fen4s.add(pos_fen4)

        best_move = None
        best_eval = -INFINITY_VAL
        best_rpv = []

        orig_alpha = alpha

        pv_move = None
        child_pv = []
        if pv:
            pv_move = pv[0]

        if DO_SEARCH_MOVE_SORT:
            moves.sort(key=lambda move: search_move_sort_key(self.board, move, pv_move), reverse=True)
                
        for move in moves:
            if move == pv_move:
                child_pv = pv[1:]
            else:
                child_pv = []
                
            self.board.push(move)
            child_best_move, child_eval, child_rpv = self.alphabeta(stats, child_pv, depth_from_root+1, depth_to_go-1, -beta, -alpha)
            self.board.pop()

            move_eval = -child_eval

            if beta <= move_eval:
                stats.n_cut_nodes += 1
                if depth_from_root != 0:
                    self.fen4s.remove(pos_fen4)
                return None, move_eval, []

            if alpha < move_eval:
                alpha = move_eval
        
            if best_eval < move_eval:
                best_move = move
                best_eval = move_eval
                child_rpv.append(move)
                best_rpv = child_rpv

        if depth_from_root != 0:
            self.fen4s.remove(pos_fen4)

        if orig_alpha < best_eval:
            stats.n_pv_nodes += 1
        else:
            stats.n_all_nodes += 1
            
        return best_move, best_eval, best_rpv
            
    def gen_move(self):
        print()
        print("Calculating...")
        stats = SearchStats(MAX_DEPTH, MAX_QDEPTH)
        # engine_move, val, rpv = self.minimax(stats, 0, MAX_DEPTH)
        engine_move, val, rpv = self.iterative_deepening(stats)
        # engine_move, val, rpv = self.alphabeta(stats, [], 0, MAX_DEPTH, -INFINITY_VAL, INFINITY_VAL)
        pv = rpv[::-1]
        return engine_move, val, pv, stats
        
class Game:
    def __init__(self, board = chess.Board()):
        self.board = board
        # TODO - separate engines for Black and White
        # TODO - docs reckon this only copies the base-board - what about previous moves?
        self.engine = Engine(board.copy())

    def play(self):
        print_board = True
        while True:
            legal_move_sans = [self.board.san(m) for m in self.board.legal_moves]
            
            print()
            
            if print_board:
                print(self.board.fen())
                # print()
                # print(self.board)
                print()
                print(self.board.unicode(invert_color=True, empty_square='.')) # Unicode chars seems backwards; Don't seem to have the default empty_square unicode in my font
                print()
            print_board = True

            if self.board.is_game_over():
                
                reason = 'unknown'
                if self.board.is_checkmate():
                    reason = 'checkmate'
                elif self.board.is_stalemate():
                    reason = 'stalemate'
                elif self.board.is_insufficient_material():
                    reason = 'insufficient material'
                elif self.board.is_seventyfive_moves():
                    reason = '75 moves played without progress'
                elif self.board.is_fivefold_repetition():
                    reason = '5-fold repetition'
                    
                print("Game over: %s (%s)" % (self.board.result(), reason))

                print()
                print("Moves: %s" % move_list_to_sans(self.board.root(), self.board.move_stack))
                return
            
            print("%s to move" % ["Black", "White"][self.board.turn])
            print()
            val = self.engine.static_eval()
            print("Static eval - positive is White advantage: %d" % val)
            # qval = self.engine.quiesce_minimax(SearchStats(MAX_DEPTH, MAX_QDEPTH), 0, val)
            # print("Quiesced eval - positive is White advantage: %d" % qval)
            print()
            print("Legal moves: %s" % " ".join(legal_move_sans))
            print()
            move_san = input("Enter move - SAN format - or 'pass' or 'engine': ")

            if move_san == "pass":
                # null move - let the other side move
                if self.board.is_check():
                    print()
                    print(">>> Illegal to 'pass' when in check <<<")
                    print_board = False
                    continue
                
                move = chess.Move.null()

            elif move_san == 'engine':
                engine_move, val, pv, stats = self.engine.gen_move()
                move_san = self.board.san(engine_move)
                # print("               ... klein skakie chooses move %s with eval %d centipawns using minimax (alphabeta) depth %d qdepth %d - PV is %s" % (move_san, val, MAX_DEPTH, MAX_QDEPTH, pv))
                # print()
                # print("nodes %d wins %d draws %d leaves %d pvs %d cuts %d alls %d nodes by depth: %s" % (stats.n_nodes, stats.n_win_nodes, stats.n_draw_nodes, stats.n_leaf_nodes, stats.n_pv_nodes, stats.n_cut_nodes, stats.n_all_nodes, " ".join([str(n) for n in stats.n_depth_nodes])))
                # print("qnodes %d qpats %d qcuts %d qnodes by depth %s" % (stats.n_qnodes, stats.n_qpat_nodes, stats.n_qcut_nodes, " ".join([str(n) for n in stats.n_qdepth_nodes])))

                move = engine_move

            else:
                if not move_san in legal_move_sans:
                    print()
                    print(">>> Illegal move \"%s\" entered <<<" % move_san)
                    print_board = False
                    continue

                move = self.board.parse_san(move_san)
                
            self.board.push(move)
            self.engine.make_move(move)

def main():
    print("Hallo RPJ - let's play chess")
    game = Game()
    game.play()

if __name__ == "__main__":
    main()
    # cProfile.run("main()")

