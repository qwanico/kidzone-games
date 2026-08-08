import asyncio
import random
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent / "sight_words_assets"
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 360
FEEDBACK_MS = 1600

BG_COLOR = (230, 245, 255)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (190, 210, 230)
SPEAKER_COLOR = (90, 160, 230)
BUTTON_COLOR = (90, 160, 230)
BUTTON_HOVER = (70, 140, 210)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (60, 90, 130)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (60, 90, 130)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def load_words():
    return sorted(p.stem for p in VOICE_DIR.glob("*.ogg"))


class Button:
    def __init__(self, rect, word):
        self.rect = pygame.Rect(rect)
        self.word = word
        self.state = "idle"

    def draw(self, surface, font, mouse_pos):
        if self.state == "correct":
            color = CORRECT_COLOR
        elif self.state == "wrong":
            color = WRONG_COLOR
        elif self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR

        pygame.draw.rect(surface, color, self.rect, border_radius=24)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=3, border_radius=24)

        text_surf = font.render(self.word, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


def draw_speaker_icon(surface, center, size, color):
    x, y = center
    body_w, body_h = size * 0.35, size * 0.5
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.center = (x - size * 0.15, y)
    pygame.draw.rect(surface, color, body_rect, border_radius=6)

    cone = [
        (x - size * 0.15 - body_w / 2, y - size * 0.15),
        (x + size * 0.05, y - size * 0.35),
        (x + size * 0.05, y + size * 0.35),
        (x - size * 0.15 - body_w / 2, y + size * 0.15),
    ]
    pygame.draw.polygon(surface, color, cone)

    for i in range(1, 3):
        radius = size * (0.18 + i * 0.14)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (x, y)
        pygame.draw.arc(
            surface, color, rect, -0.5, 0.5, width=5
        )


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sight Words")

        self.font_word = pygame.font.SysFont("arial", 48, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 50, bold=True)
        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_reveal = pygame.font.SysFont("arial", 90, bold=True)

        self.words = load_words()
        if len(self.words) < 2:
            raise RuntimeError("Need at least 2 sight words in voice_cache/")

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.last_word = None
        self.last_wrong = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_word = None
        self.reveal_word = False

        self.card_rect = pygame.Rect(0, 0, CARD_SIZE, CARD_SIZE)
        self.card_rect.centerx = WIDTH // 2
        self.card_rect.top = 60

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

    def start_game(self):
        self.state = STATE_PLAYING
        self.new_round()

    def enter_pause(self):
        ticks = pygame.time.get_ticks()
        self._pause_remaining = (self.feedback_until - ticks) if self.feedback_until > ticks else None
        pygame.mixer.music.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = ticks + self._pause_remaining if self._pause_remaining else 0
        pygame.mixer.music.unpause()
        self.state = STATE_PLAYING

    def speak(self, word):
        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(VOICE_DIR / f"{word}.ogg"))
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()

    def new_round(self):
        choices = [w for w in self.words if w != self.last_word] or self.words
        self.current_word = random.choice(choices)
        self.last_word = self.current_word

        wrong_choices = [
            w for w in self.words
            if w != self.current_word and w != self.last_wrong
        ] or [w for w in self.words if w != self.current_word]
        wrong_word = random.choice(wrong_choices)
        self.last_wrong = wrong_word

        pair = [self.current_word, wrong_word]
        random.shuffle(pair)

        button_w, button_h = 320, 90
        gap = 40
        total_w = button_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - 160

        self.buttons = [
            Button((start_x, y, button_w, button_h), pair[0]),
            Button((start_x + button_w + gap, y, button_w, button_h), pair[1]),
        ]
        self._button_names = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.reveal_word = False

        self.speak(self.current_word)

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_click(self, pos):
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()
            return

        if self.card_rect.collidepoint(pos):
            self.speak(self.current_word)
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, word in zip(self.buttons, self._button_names):
            if button.rect.collidepoint(pos):
                is_correct = word == self.current_word
                for b, w in zip(self.buttons, self._button_names):
                    b.state = "correct" if w == self.current_word else (
                        "wrong" if b is button else "idle"
                    )

                self.reveal_word = True

                if is_correct:
                    self.score += 1
                    self.streak += 1
                    self.feedback_text = "Great job!"
                    self.feedback_color = CORRECT_COLOR
                else:
                    self.streak = 0
                    self.wrong_sound.play()
                    self.feedback_text = f'That word is "{self.current_word}"'
                    self.feedback_color = WRONG_COLOR

                self.feedback_until = pygame.time.get_ticks() + FEEDBACK_MS
                return

    def update(self):
        if self.feedback_until and pygame.time.get_ticks() >= self.feedback_until:
            self.new_round()

    def draw_menu(self):
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Sight Words", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 220))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_subtitle.render(
            "Listen, then click the word you hear!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 290))
        self.screen.blit(subtitle_surf, subtitle_rect)

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_playing(self):
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        card_rect = self.card_rect
        border_color = BUTTON_HOVER if card_rect.collidepoint(mouse_pos) else CARD_BORDER
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=28)
        pygame.draw.rect(self.screen, border_color, card_rect, width=3, border_radius=28)

        if self.reveal_word and pygame.time.get_ticks() < self.feedback_until:
            word_surf = self.font_reveal.render(self.current_word, True, self.feedback_color)
            word_rect = word_surf.get_rect(center=card_rect.center)
            self.screen.blit(word_surf, word_rect)
        else:
            draw_speaker_icon(self.screen, card_rect.center, CARD_SIZE * 0.5, SPEAKER_COLOR)

        for button in self.buttons:
            button.draw(self.screen, self.font_word, mouse_pos)

        score_text = self.font_score.render(
            f"Score: {self.score}   Streak: {self.streak}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (24, 20))

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos)

        if self.feedback_text and pygame.time.get_ticks() < self.feedback_until:
            fb_surf = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, card_rect.bottom + 40))
            self.screen.blit(fb_surf, fb_rect)

    def draw_paused(self):
        mouse_pos = pygame.mouse.get_pos()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        paused_surf = self.font_title.render("Paused", True, (255, 255, 255))
        paused_rect = paused_surf.get_rect(center=(WIDTH // 2, 240))
        self.screen.blit(paused_surf, paused_rect)

        self.resume_button.draw(self.screen, self.font_word, mouse_pos)
        self.quit_button.draw(self.screen, self.font_word, mouse_pos)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()

        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.enter_pause()
                    elif self.state == STATE_PAUSED:
                        self.resume_game()
                    else:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(Game().run())
