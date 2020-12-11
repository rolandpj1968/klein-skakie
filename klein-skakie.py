import time
import sys

import chess

from util import fen4, move_list_to_sans

import evaluate

from engine import Engine

import cProfile

class Game:
    def __init__(self, board = chess.Board(), engine_time_allowed_s = 0):
        self.board = board
        # TODO - docs reckon this only copies the base-board - what about previous moves?
        print("!!!!!!!!!!!!!!! engine time allowed is %.3fs" % engine_time_allowed_s)
        self.engines = [Engine(board.copy(), engine_time_allowed_s), Engine(board.copy(), engine_time_allowed_s)]

    def play(self):
        total_engine_time_s = 0
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
            w_val = self.engines[chess.WHITE].static_eval()
            b_val = self.engines[chess.BLACK].static_eval()
            print("Static eval - positive is White advantage: white engine %d cp black engine %d cp" % (w_val, b_val))
            # qval = self.engine.quiesce_alphabeta(SearchStats(MAX_DEPTH, MAX_QDEPTH), 0, val)
            # print("Quiesced eval - positive is White advantage: %d" % qval)
            print()
            print("Legal moves: %s" % " ".join(legal_move_sans))
            print()
            move_san = input("Enter move - SAN format - or 'pass' or 'engine': ")
            print()

            if move_san == "pass":
                # null move - let the other side move
                if self.board.is_check():
                    print()
                    print(">>> Illegal to 'pass' when in check <<<")
                    print_board = False
                    continue
                
                move = chess.Move.null()

            elif move_san == 'engine':
                engine = self.engines[self.board.turn]
                engine_move, val, pv, stats = engine.gen_move()
                
                move = engine_move

            else:
                if not move_san in legal_move_sans:
                    print()
                    print(">>> Illegal move \"%s\" entered <<<" % move_san)
                    print_board = False
                    continue

                move = self.board.parse_san(move_san)
                
            self.board.push(move)
            self.engines[chess.WHITE].make_move(move)
            self.engines[chess.BLACK].make_move(move)

def main():
    print("Hallo RPJ - let's play chess")
    # game = Game(chess.Board(), 3*60)
    # game = Game(chess.Board())
    # game = Game(chess.Board("2r1r1k1/2bn4/R1p1p3/2P2p1p/1P3P2/3B2PP/8/2BR2K1 w - - 1 32"))
    game = Game(chess.Board("r1bqk2r/ppp2ppp/2nbpn2/3p4/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 2 6"))
    game.play()

if __name__ == "__main__":
    main()
    # cProfile.run("main()")

