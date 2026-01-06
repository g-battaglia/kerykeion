# TODO – Development Roadmap

**Legend:**

-   `[ ]` – To do
-   `[>]` – In progress
-   `[x]` – Completed
-   `[KO]` – Removed / No longer needed

**Priority levels:**

-   🟥 High
-   🟧 Medium
-   🟨 Low

---

## Version 5 Tasks

### 🟥 High Priority

### 🟧 Medium Priority

-   [ ] Support BCE dates
-   [ ] Discepolo's Score in Synastry
-   [ ] **Egyptian Terms and Chaldean Decans** - Add essential dignities support
    -   **Background**: Mail Object: "How to draw egipty terms and decans in the Wheel"
    -   **Egyptian Terms (Bounds)**: 5 unequal divisions per sign, each ruled by Mercury/Venus/Mars/Jupiter/Saturn
    -   **Chaldean Decans (Faces)**: 3 equal 10° divisions per sign, following Chaldean planetary order
    -   **Implementation**:
        -   [ ] Create `kerykeion/dignities/` module with:
            -   [ ] `decan_utils.py` - Chaldean decan calculation functions
            -   [ ] `term_utils.py` - Egyptian terms lookup and calculation
            -   [ ] `dignity_data.py` - Complete reference tables for all 12 signs
        -   [ ] Add optional fields to `KerykeionPointModel`: `decan_number`, `decan_ruler`, `term_ruler`
        -   [ ] Update `AstrologicalSubjectFactory` to optionally calculate dignities
        -   [ ] Add unit tests for all dignity calculations
        -   [ ] Add documentation for the new features

### 🟨 Low Priority

-   [ ] Implement Gauquelin Sector as an additional house system mode (`G`)
-   [ ] Create unit tests for polar circle edge cases
-   [ ] `get_trasnlation` function for multiple languages
