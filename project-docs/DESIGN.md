# UI/UX Brief — Utsav AI

- **Direction:** festive but calm — navy text on cream, saffron accents, diya icon. Original artwork only.
- **IA:** sidebar = input form; main = 6 tabs: Overview → Budget → Timeline → Vendors → Ideas → Export.
- **Flow:** fill form → *Create my plan* → Overview shows days-to-go, per-guest cost, warnings, next 3 tasks.
- **States:** empty (info prompt), loading (spinner), error (per-field messages, all at once), success (tabs), AI-unavailable (caption label on Ideas).
- **Accessibility:** labelled inputs, help text, chart + table, icons never carry meaning alone, contrast ≥ 5.3:1, keyboard-operable, skip link on web shell.
- **Responsive:** Streamlit wide layout collapses sidebar on mobile; PWA shell is full-height.
- **Watermark:** KP logo in the footer (`assets/logo-mark.svg`).
