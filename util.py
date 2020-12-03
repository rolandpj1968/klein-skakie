
# FEN representation of the board with the half-move and full-move counts removed
# Used for repeated position checks
def fen4(board):
    return " ".join(board.fen().split()[:4])

# Generate SAN string list from sequence of moves starting from the given board position
def move_list_to_sans(orig_board, moves):
    board = orig_board.copy()
    
    sans = []
    for move in moves:
        sans.append(board.san(move))
        board.push(move)

    return sans

