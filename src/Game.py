import pygame
import random
import time
import os
from const import *
from board import Board
from dragger import Dragger
from square import Square
from sound import Sound

class Game:
    def __init__(self):
        self.board = Board()
        self.dragger = Dragger()
        self.next_player = 'white'
        self.hovered_sq = None
        self.game_over = False
        self.winner = None
        self.last_move = None
        
        # Cores do tabuleiro
        self.bg_light_color = (234, 235, 200)
        self.bg_dark_color = (119, 154, 88)
        self.move_light_color = (220, 220, 220, 150)
        self.move_dark_color = (150, 150, 150, 150)
        self.trace_light_color = (255, 255, 0, 150)
        self.trace_dark_color = (255, 255, 0, 150)

        # Carrega as imagens das peças
        self.pieces_images = self.load_assets()
        
    def play_move(self, piece, move):
        initial, final = move.initial, move.final
        
        # Verifica se o movimento é uma captura para tocar o som correto
        captured = self.board.squares[final.row][final.col].has_piece()
        
        self.board.move(piece, move)
        self.last_move = move
        self.play_sound(captured)
        self.next_player = 'black' if self.next_player == 'white' else 'white'
        
        # Verifica a condição de fim de jogo após a jogada
        game_state = self.board.check_game_over(self.next_player)
        if game_state:
            self.game_over = True
            if game_state == 'checkmate':
                self.winner = 'white' if self.next_player == 'black' else 'black'
            else: # empate por afogamento
                self.winner = None
    
    def ai_move(self):
        # Atraso para dar uma sensação de "pensamento"
        time.sleep(1.0)
        
        legal_moves = []
        for row in range(ROWS):
            for col in range(COLS):
                square = self.board.squares[row][col]
                if square.has_piece() and square.piece.color == 'black':
                    piece = square.piece
                    self.board.calc_moves(piece, row, col)
                    for move in piece.moves:
                        legal_moves.append((piece, move))
        
        if legal_moves:
            # Escolhe um movimento aleatório
            chosen_move = random.choice(legal_moves)
            chosen_piece, chosen_move_obj = chosen_move
            
            self.play_move(chosen_piece, chosen_move_obj)

    # ==================== MÉTODOS DE RENDERIZAÇÃO ====================
    def show_bg(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                color = self.bg_light_color if (row + col) % 2 == 0 else self.bg_dark_color
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

                # Desenha coordenadas de linha
                if col == 0:
                    color = self.bg_dark_color if row % 2 == 0 else self.bg_light_color
                    font = pygame.font.SysFont('monospace', 14, bold=True)
                    lbl = font.render(str(ROWS - row), 1, color)
                    lbl_pos = (5, 5 + row * SQSIZE)
                    surface.blit(lbl, lbl_pos)

                # Desenha coordenadas de coluna
                if row == 7:
                    color = self.bg_dark_color if (row + col) % 2 == 0 else self.bg_light_color
                    font = pygame.font.SysFont('monospace', 14, bold=True)
                    lbl = font.render(Square.get_alphacol(col), 1, color)
                    lbl_pos = (col * SQSIZE + SQSIZE - 20, HEIGHT - 20)
                    surface.blit(lbl, lbl_pos)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if piece is not self.dragger.piece:
                        piece.set_texture(size=80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        if self.dragger.dragging:
            piece = self.dragger.piece
            for move in piece.moves:
                color = self.move_light_color if (move.final.row + move.final.col) % 2 == 0 else self.move_dark_color
                rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)
                
    def show_last_move(self, surface):
        if self.last_move:
            initial = self.last_move.initial
            final = self.last_move.final
            for pos in [initial, final]:
                color = self.trace_light_color if (pos.row + pos.col) % 2 == 0 else self.trace_dark_color
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect, width=4)

    def show_hover(self, surface):
        if self.hovered_sq:
            color = (180, 180, 180)
            rect = (self.hovered_sq.col * SQSIZE, self.hovered_sq.row * SQSIZE, SQSIZE, SQSIZE)
            pygame.draw.rect(surface, color, rect, width=3)

    # ==================== OUTROS MÉTODOS ====================
    def load_assets(self):
        assets = {}
        # Obtém o diretório do script atual (game.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Volta um nível para chegar à pasta raiz do projeto (Chess-AI-Py)
        base_dir = os.path.dirname(current_dir)
        
        for color in ['white', 'black']:
            assets[color] = {}
            for piece_name in ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']:
                # Cria o caminho completo para o arquivo da imagem
                file_path = os.path.join(base_dir, 'assets', 'images', 'imgs-80px', f'{piece_name}_{color}.png')
                
                # Verifique se o arquivo existe antes de carregar
                if not os.path.exists(file_path):
                    print(f"Erro: Arquivo não encontrado em {file_path}")
                    return {}
                
                image = pygame.image.load(file_path).convert_alpha()
                image = pygame.transform.scale(image, (SQSIZE, SQSIZE))
                assets[color][piece_name] = image
        return assets
    
    def play_sound(self, captured=False):
        try:
            if captured:
                Sound(os.path.join('assets/sounds/capture.wav')).play()
            else:
                Sound(os.path.join('assets/sounds/move.wav')).play()
        except pygame.error:
            # Caso os arquivos de som não sejam encontrados
            print("Aviso: Arquivos de som não encontrados.")

    def set_hover(self, row, col):
        self.hovered_sq = self.board.squares[row][col]
    
    def change_theme(self):
        # Esta função precisa de uma implementação mais completa se você quiser mudar o tema
        pass

    def reset(self):
        self.__init__()