# TODO – Development Roadmap

**Legend:**

- `[ ]` – To do
- `[>]` – In progress
- `[x]` – Completed
- `[KO]` – Removed / No longer needed

**Priority levels:**

- 🟥 High
- 🟧 Medium
- 🟨 Low

---

## Version 5 Tasks

### 🟥 High Priority

- [x] Rename "Return" and "SingleWheelReturn" to "DualReturnChart" and "SingleReturnChart"
- [x] Rename "makeSVG", "makeTemplate" and similar methods to more clear names.
- [x] Path inside the write svg method
- [x] Better default chart title (Synastry, Transits)
- [x] Configurable chart title from save_svg()
- [x] Fix day of week translation
- [x] Correct the displayed file name (browser tab/title)
- [x] Expand unit tests to cover all aspects of the library
- [x] Complete all the arab parts and other points in the chart
- [x] Correct the ChartDataFactory: it should auto calculate the active points.
- [x] Fix: grid style synastry
- [x] Fix: all/many points chart, maybe just add a warning for max n points
- [x] Fix: file path for svg
- [x] Fix: Create correct glifs for all the points
- [x] Fix: Synastry charts ad Score should have more orbit for axes
- [x] Feat: test all points just grid chart

- [~] Full documentation for the library
- [ ] Fix: Spica glif
- [ ] Fix: Dual charts
- [ ] Doc snippets check and fix
- [ ] docs: Return charts

### 🟧 Medium Priority

- [ ] More "air space" around objects in the chart
- [ ] Discepolo's Score in Synastry

### 🟨 Low Priority

- [ ] Implement Gauquelin Sector as an additional house system mode (`G`)
- [ ] Create unit tests for polar circle edge cases
- [ ] `get_trasnlation` function for multiple languages
