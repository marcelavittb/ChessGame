import copy
import os
from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound

class Board:

    def __init__(self):
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.last_move = None
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    # ==================== MOVE EXECUTION ====================
    def move(self, piece, move, testing=False):
        initial, final = move.initial, move.final
        en_passant_empty = self.squares[final.row][final.col].isempty()

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        # pawn specific moves
        if isinstance(piece, Pawn):
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                self.squares[initial.row][final.col].piece = None
            
            self.check_promotion(piece, final)

        # king castling
        if isinstance(piece, King) and self.castling(initial, final):
            diff = final.col - initial.col
            rook = piece.left_rook if (diff < 0) else piece.right_rook
            self.move(rook, rook.moves[-1], testing=testing)

        piece.moved = True
        piece.clear_moves()
        self.last_move = move
        
        if not testing:
            if en_passant_empty:
                Sound(os.path.join('assets/sounds/move.wav')).play()
            else:
                Sound(os.path.join('assets/sounds/capture.wav')).play()
        
        # Seta o en passant para o peão
        if isinstance(piece, Pawn) and abs(final.row - initial.row) == 2:
            self.set_true_en_passant(piece)
        else:
            for row in range(ROWS):
                for col in range(COLS):
                    sq = self.squares[row][col]
                    if isinstance(sq.piece, Pawn):
                        sq.piece.en_passant = False

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn):
            return
        
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.has_piece() and isinstance(square.piece, Pawn):
                    square.piece.en_passant = False
        
        piece.en_passant = True

    # ==================== CHECK ====================
    def is_in_check(self, color, board=None):
        temp_board = board if board else self
        
        king = None
        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(temp_board.squares[row][col].piece, King) and \
                   temp_board.squares[row][col].piece.color == color:
                    king = temp_board.squares[row][col].piece
                    king_row, king_col = row, col
                    break
            if king:
                break
        
        if not king:
            return False

        for row in range(ROWS):
            for col in range(COLS):
                square = temp_board.squares[row][col]
                if square.has_enemy_piece(color):
                    p = square.piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        return False
    
    def in_check(self, piece, move):
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        
        return temp_board.is_in_check(temp_piece.color)


    # ==================== MOVE CALCULATION ====================
    def calc_moves(self, piece, row, col, bool=True):
        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end = row + (piece.dir * steps)
            direction = piece.dir

            for r in range(start, end + direction, direction):
                if not Square.in_range(r):
                    break
                if self.squares[r][col].isempty():
                    initial = Square(row, col)
                    final = Square(r, col)
                    move = Move(initial, final)
                    if bool and self.in_check(piece, move):
                        continue
                    piece.add_move(move)
                else:
                    break

            for dc in [-1, 1]:
                r = row + direction
                c = col + dc
                if Square.in_range(r, c):
                    if self.squares[r][c].has_enemy_piece(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[r][c].piece
                        final = Square(r, c, final_piece)
                        move = Move(initial, final)
                        if bool and self.in_check(piece, move):
                            continue
                        piece.add_move(move)

            r_en_passant = 3 if piece.color == 'white' else 4
            r_final = 2 if piece.color == 'white' else 5
            if row == r_en_passant:
                for dc in [-1, 1]:
                    c = col + dc
                    if Square.in_range(c):
                        sq = self.squares[row][c]
                        if (sq.has_enemy_piece(piece.color) and 
                            isinstance(sq.piece, Pawn) and 
                            sq.piece.en_passant):
                            initial = Square(row, col)
                            final = Square(r_final, c)
                            move = Move(initial, final)
                            if bool and self.in_check(piece, move):
                                continue
                            piece.add_move(move)

        def knight_moves():
            deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in deltas:
                r, c = row + dr, col + dc
                if Square.in_range(r, c):
                    if self.squares[r][c].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[r][c].piece
                        final = Square(r, c, final_piece)
                        move = Move(initial, final)
                        if bool and self.in_check(piece, move):
                            continue
                        piece.add_move(move)

        def straightline_moves(directions):
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while Square.in_range(r, c):
                    sq = self.squares[r][c]
                    initial = Square(row, col)
                    final_piece = sq.piece
                    final = Square(r, c, final_piece)
                    move = Move(initial, final)
                    
                    if sq.isempty():
                        if bool and self.in_check(piece, move):
                            pass
                        else:
                            piece.add_move(move)
                    elif sq.has_enemy_piece(piece.color):
                        if bool and self.in_check(piece, move):
                            pass
                        else:
                            piece.add_move(move)
                        break
                    else:
                        break
                    
                    r += dr
                    c += dc

        def king_moves():
            adjs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in adjs:
                r, c = row + dr, col + dc
                if Square.in_range(r, c):
                    sq = self.squares[r][c]
                    if sq.isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final_piece = sq.piece
                        final = Square(r, c, final_piece)
                        move = Move(initial, final)
                        if bool and self.in_check(piece, move):
                            continue
                        piece.add_move(move)

            # Castling
            if not bool:
                return
                
            if not piece.moved:
                # Queenside (left) castling
                left_rook = self.squares[row][0].piece
                if (isinstance(left_rook, Rook) and not left_rook.moved and
                    all(self.squares[row][c].isempty() for c in range(1, 4))):
                    
                    if not self.is_in_check(piece.color) and \
                       not self.in_check(piece, Move(Square(row, col), Square(row, 2))):
                        final_king = Square(row, 2)
                        move_king = Move(Square(row, col), final_king)
                        piece.add_move(move_king)
                        piece.left_rook = left_rook

                # Kingside (right) castling
                right_rook = self.squares[row][7].piece
                if (isinstance(right_rook, Rook) and not right_rook.moved and
                    all(self.squares[row][c].isempty() for c in range(5, 7))):
                    
                    if not self.is_in_check(piece.color) and \
                       not self.in_check(piece, Move(Square(row, col), Square(row, 6))):
                        final_king = Square(row, 6)
                        move_king = Move(Square(row, col), final_king)
                        piece.add_move(move_king)
                        piece.right_rook = right_rook

        piece.clear_moves()
        if isinstance(piece, Pawn):
            pawn_moves()
        elif isinstance(piece, Knight):
            knight_moves()
        elif isinstance(piece, Bishop):
            straightline_moves([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif isinstance(piece, Rook):
            straightline_moves([(-1, 0), (0, 1), (1, 0), (0, -1)])
        elif isinstance(piece, Queen):
            straightline_moves([
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1), (0, 1),
                (1, -1), (1, 0), (1, 1)
            ])
        elif isinstance(piece, King):
            king_moves()

    # ==================== GAME OVER ====================
    def check_game_over(self, color):
        has_legal_moves = False
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.has_piece() and square.piece.color == color:
                    piece = square.piece
                    self.calc_moves(piece, row, col)
                    if piece.moves:
                        has_legal_moves = True
                        break
            if has_legal_moves:
                break
        
        if not has_legal_moves:
            if self.is_in_check(color):
                return 'checkmate'
            else:
                return 'stalemate'
        return None

    # ==================== BOARD SETUP ====================
    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        self.squares[row_other][3] = Square(row_other, 3, Queen(color))
        self.squares[row_other][4] = Square(row_other, 4, King(color))