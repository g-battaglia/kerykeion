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

- [ ] Fix labels  (eg. "Aspetti Tra [...]")  
- [x] Refactor structure using the new `AstrologicalSubjectModel` and a factory class to instantiate objects in multiple ways:
  - [ ] Online  
  - [ ] Offline  
  - [ ] With UTC ISO 8601 string  
  - [ ] With current UTC time  
  - [ ] With only active planets  
- [ ] Discepolo's Score in Synastry
- [x] Add weekday name to the output  
- [ ] Add planetary speed and direction  
- [ ] Create utility function to retrieve all active planets  
- [ ] Full documentation for the library and AstrologerAPI
- [ ] More "air space" around objects in the chart
- [ ] More colorful themes (eg. "strawberry")
- [ ] Correct the displayed file name (browser tab/title)
- [ ] NatalAspects and SynatryAspect with inheritance of ActivePoints


### 🟧 Medium Priority

- [ ] Implement Gauquelin Sector as an additional house system mode (`G`)
- [ ] Finalize and integrate new examples into the documentation  

### 🟨 Low Priority

- [ ] Create unit tests for polar circle edge cases
- [ ] `get_trasnlation` function for multiple languages


