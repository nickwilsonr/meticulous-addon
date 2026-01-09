# Contributing to Meticulous Home Assistant Add-on

**For:** Developers and contributors
**Audience:** Anyone wanting to contribute code, fix bugs, or enhance the add-on

Thank you for your interest in contributing! This is the entry point for all developer-related information.

---

## Developer Quick Links

- [Development Guide](development.md) — Setup, testing, architecture overview, roadmap
- [Architecture & Integration](architecture.md) — Technical deep dive, sensor specs, implementation details
- [Main README](../README.md) — What end-users see (useful context)

---

## Getting Started

1. **Fork and clone:**
   ```bash
   git clone https://github.com/yourusername/meticulous-addon.git
   cd meticulous-addon
   ```

2. **Set up development environment:**
   See [docs/development.md](docs/development.md) for setup instructions.

3. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature-name
   ```

---

## Code Style

- **Python**: PEP 8 with type hints
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- **Documentation**: Update relevant docs when adding features
- **Tests**: Add tests for new functionality (when test framework is set up)

---

## Making Changes

1. **Make your changes** in your feature branch
2. **Test thoroughly:**
   - Run locally against your Meticulous machine
   - Verify Socket.IO connection and events
   - Check MQTT entity creation
   - Test any new services/commands
3. **Update CHANGELOG.md** with your changes
4. **Commit with conventional format:**
   ```bash
   git commit -m "feat: add new sensor for water temp"
   git commit -m "fix: reconnection fails after timeout"
   git commit -m "docs: clarify MQTT configuration"
   ```

---

## Submitting Pull Requests

1. **Push to your fork:**
   ```bash
   git push origin feature/my-feature-name
   ```

2. **Create PR on GitHub** with:
   - Clear title describing the change
   - Description of what changed and why
   - Any relevant issue numbers (fixes #123)
   - Screenshots or logs if applicable

3. **Address review feedback** and update your branch

---

## Types of Contributions

### Reporting Issues
- Describe the problem clearly
- Include logs and configuration
- Specify your Home Assistant and add-on version
- Provide steps to reproduce

### Improving Documentation
- Fix typos or unclear explanations
- Add examples or troubleshooting steps
- Clarify configuration options
- Submit as PR to `/docs`

### Adding Features
- Discuss in an issue first (or start a discussion)
- Follow the roadmap in [docs/development.md](docs/development.md)
- Ensure it aligns with the add-on's scope
- Update relevant documentation

### Fixing Bugs
- Create an issue describing the bug
- Reference it in your PR
- Include a test case if possible

---

## Development Notes

### Socket.IO Integration
- Real-time updates use Socket.IO events
- Implement event handlers in `run.py`
- Add corresponding sensors for verification

### MQTT Discovery
- New sensors should auto-discover via MQTT
- Include device_class and units
- Test with Home Assistant's MQTT integration

### Configuration
- Add new options to `config.json`
- Document in `docs/user-guide.md`
- Provide sensible defaults

### Testing
- Test locally with your Meticulous machine
- Verify Socket.IO connectivity and reconnection
- Check MQTT entity creation
- Test with minimal and verbose logging

---

## Before Submitting

- [ ] Code follows PEP 8
- [ ] Type hints added
- [ ] Docstrings included
- [ ] CHANGELOG.md updated
- [ ] Tested locally against real machine
- [ ] Documentation updated if applicable
- [ ] Commit messages are conventional format

---

## Questions?

- Check [docs/development.md](docs/development.md)
- Review existing issues and PRs
- Ask in your PR or create a discussion

---

## License

By contributing, you agree your code is licensed under the MIT License (see LICENSE file).
