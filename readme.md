# MjCord

MjCord is a Discord bot that enables four players to play Hong Kong–style Mahjong entirely through Discord direct messages. The bot manages game state, enforces rules, resolves move priority, and calculates scoring, allowing players to focus on gameplay without manual bookkeeping.

The project is built as a self-contained Discord bot with no external UI or services.

---

## Overview

MjCord provides a complete turn-based Mahjong experience inside Discord:

- Four-player Hong Kong Mahjong
- Private, DM-based hands and actions
- Automatic move validation and priority resolution
- Win detection and faan-based scoring
- Persistent player rating system

All game logic is handled by the bot, from tile dealing to round completion.

---

## Gameplay

A typical round proceeds as follows:

1. Four players join a game.
2. Tiles are shuffled and dealt automatically.
3. Each player receives their hand and game state via direct messages.
4. On each turn, players interact using Discord buttons to:
   - Discard tiles
   - Claim Chow, Pong, or Kong
   - Declare a win (Hu)
5. The bot validates actions, resolves conflicts, and advances the game state.
6. When a round ends, scores and ratings are updated and players vote on whether to continue.

---

## Features

- Full Hong Kong Mahjong ruleset
- Automated win detection and faan calculation (capped at 13)
- Support for flowers and seasons
- Button-based interaction (no text input during play)
- DM-only gameplay to prevent information leakage
- Vote-based session control
- Persistent Elo ratings across games

---

## Commands

| Command | Description |
|--------|-------------|
| `!run` | Start a new Mahjong game |
| `!queue` | Join the matchmaking queue |
| `!quit` | Vote to end the current game |
| `!h` | Display available commands |

---

## Supported Winning Hands

The following is a non-exhaustive list of supported winning hands:

- All Sequences (平糊)
- All Triplets (碰碰糊)
- Seven Pairs (七對子)
- Thirteen Orphans (十三幺)
- Nine Gates (九子連環)
- Pure Flush (清一色)
- Mixed Flush (混一色)
- Big / Small Three Dragons (大三元 / 小三元)
- Big / Small Four Winds (大四喜 / 小四喜)
- Heavenly / Earthly / Human Hand (天糊 / 地糊 / 人糊)

Maximum scoring is capped at 13 faan.

---

## Player Ratings

- Each player is assigned an Elo rating
- New players start at a rating of 1000
- Ratings are updated after each completed round
- Ratings persist across sessions

---

## Design Considerations

- Strictly four-player gameplay
- No public exposure of hands or private state
- No external dependencies beyond Discord
- Emphasis on correctness and rule enforcement
- Designed for asynchronous, turn-based interaction

---

## Project Status

MjCord is an active personal project.  
Rules, scoring, and flow may change as the implementation evolves.

Issues and improvement suggestions are welcome.
