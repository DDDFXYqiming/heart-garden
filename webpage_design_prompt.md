# Interface design reference

The visual reference uses paper-like surfaces, irregular borders and restrained handwritten accents. This document describes presentation choices for the existing application.

## Palette

| Role | Colour |
|---|---|
| Background | `#fdfbf7` |
| Text and borders | `#2d2d2d` |
| Muted surface | `#e5e0d8` |
| Primary accent | `#ff4d4d` |
| Secondary accent | `#2d5da1` |
| Note surface | `#fff9c4` |

## Components

Cards and buttons use irregular corner radii with small hard-offset shadows. Slight rotation and paper textures are decorative accents and should not interfere with reading or interaction. Inputs use clear borders and visible focus states.

Kalam and Patrick Hand are the reference display typefaces. Body text and controls need readable fallback fonts. Shared colour, spacing and border values belong in reusable styles rather than duplicated component rules.

## Layout and accessibility

Small screens use a single-column layout where needed, with comfortable touch targets and no horizontal overflow. Keyboard focus, labels and contrast remain visible in every interactive state. Motion should be brief and respect reduced-motion preferences.
