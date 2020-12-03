import chess

import evaluate

DO_USE_ID_TT = False
DO_USE_ID_PV = True

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
def search_move_sort_key(board, move, pv_move, tt_move):
    if DO_USE_ID_PV and move == pv_move:
        return SEARCH_MOVE_PV_MOVE

    if DO_USE_ID_TT and move == tt_move:
        return SEARCH_MOVE_TT_MOVE
    
    moving_piece_type = board.piece_type_at(move.from_square)
    is_capture = board.is_capture(move)
    is_target_attacked = board.is_attacked_by(not board.turn, move.to_square)

    moving_piece_val = evaluate.PIECE_VALS[chess.WHITE][moving_piece_type]
    moving_piece_pp = evaluate.PIECE_POS_VALS[board.turn][moving_piece_type]
    pp_delta = (moving_piece_pp[move.to_square] - moving_piece_pp[move.from_square]) * [-1, 1][board.turn]

    if is_capture:
        captured_piece_type = board.piece_type_at(move.to_square)
        if board.is_en_passant(move):
            captured_piece_type = chess.PAWN

        captured_piece_val = evaluate.PIECE_VALS[chess.WHITE][captured_piece_type]
        
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

    
