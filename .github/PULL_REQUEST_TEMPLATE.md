<!-- 
Thank you for contributing! Please fill out this template to help us review your PR.
-->

## 📝 Description

As per some of our issues, we will need several forms of data extracted from files in order to attribute any values to them.

For a starting point, I turned to RAKE in order to have a basic keyword extraction system for base level text files. RAKE is mostly automated, but is useful in extracting what is actually of value out of blocks of text, so I figured it would work just fine for the project.

Note that you will need to use pip to install RAKE as such:

`pip install rake-nltk nltk`

Running this in the terminal should set everything up properly. The program itself downloads any other relevant functions.

Aside from this, testConsole.py is updated to guide through basic manual testing for the functionality, so:

`python src/testConsole.py`

Running this should be self explanatory, just choose option 3. 

Test files are also in place, so run as required.

**Closes:** # 52

---

## 🔧 Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation added/updated
- [ ] ✅ Test added/updated
- [ ] ♻️ Refactoring
- [ ] ⚡ Performance improvement

---

## 🧪 Testing

Just manual testing as again, this is a file intended to be replaced. Tested all input options and seem to be working fine.

- [✓] test_keywordExtractor_unittest.py

---

## ✓ Checklist

- [x] 🤖 GenAI was used in generating the code and I have performed a self-review of my own code
- [x] 💬 I have commented my code where needed
- [ ] 📖 I have made corresponding changes to the documentation
- [x] ⚠️ My changes generate no new warnings
- [x] ✅ I have added tests that prove my fix is effective or that my feature works and tests are passing locally
- [ ] 🔗 Any dependent changes have been merged and published in downstream modules
- [ ] 📱 Any UI changes have been checked to work on desktop, tablet, and/or mobile

---

## 📸 Screenshots

> If applicable, add screenshots to help explain your changes

<details>
<summary>Click to expand screenshots</summary>

<!-- Add your screenshots here -->

</details>
