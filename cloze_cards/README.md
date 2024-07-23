# Anki Cloze Cards Formats

This folder contains the html code for anki cards, featuring:

- **Target Language**
  - `front` field contains the target word
  - A random picked example from the `example` field (separated by the `|` character)
- **Translation**
  - `back` field containing a plain string for the meaining
  - A random picked example from the `example` field. This time, the target word is occluded.
  - `translations` field containing json objects. These will be formatted dynamically to html and contain information about meanings:
    - the type of the word (part of speech)
    - the meanings
    - the etymology
    - potential examples of the meanings
    - TODO: These should be collapsible:

```html
<details>
    <summary>Click to toggle</summary>
    <span>Oh, hello</span>
</details>
```

- TODO: perphaps create html elements for display(numbered list for pos, unordered list for examples etc.)
