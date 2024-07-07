# TODO

Legend:

- `[ ]` - Task to be done
- `[>]` - Task in progress
- `[x]` - Task completed

## Tasks

- [x] Fix the unit tests. The code is working but the tests must be updated to the new features.
- [ ] Create unit test for checking polar circle
- [ ] Finish the new examples to be added to the documentation
- [>] Create a complete documentation (Vitepress) with all the examples: https://www.kerykeion.net/docs/examples/birth-chart

- [ ] Fix Settings in a way to accept a dictionary with the settings and not just a JSON file and write docs.
- [>] Create new AstrologicalSubject argument for House System mode.
  - [ ] Implement unit tests for the House System mode.
  - [ ] Implement Gauquelin Sector as House System mode (G).
- [ ] Create new AstrologicalSubject argument for Position Mode (Geocentric, Heliocentric, Topocentric, etc).
- [ ] Implement week day name.

## V5

- [ ] New structure based on the new AstrologicalSubjectModel and a factory class to create the objects in different ways:

  - [ ] Online
  - [ ] Offline
  - [ ] With UTC ISO 8601 string
  - [ ] For now at UTC time

- [ ] New utility function to get all active planets, so we can remove aspect/planet list and use just the AstrologicalSubjectModel structure.

- [ ] New way of setting the language, with an object representing the labels and the texts.
