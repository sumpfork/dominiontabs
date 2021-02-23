# Translation Instructions

## File Format
    /card_db/
            xx/
               bonuses_xx.json
               cards_xx.json
               sets_xx.json
               types_xx.json

where xx is ISO 639-1 standard language code in lower case with under bar '_' replacing dash '-'
Please rename the directory and the files to match the language you are providing.


## Character encoding
The files:

    bonuses_xx.json
    cards_xx.json
    sets_xx.json
    types_xx.json

must be encoded in ISO 8859-15, also known as  "Latin alphabet no. 9"
This character set is used throughout the Americas, Western Europe, Oceania, and much of Africa.
It is also commonly used in most standard romanizations of East-Asian languages.

If you have a language that is not supported by ISO 8859-15 please contact the developers by [creating a new issue](https://github.com/sumpfork/dominiontabs/issues/new).


## Anatomy of sets_xx.json
Entries in this file represent Dominion sets/expansions.  A typical entry looks like:

    "alchemy": {
        "set_name": "Alchimia",
        "text_icon": "Al"
    },

- The set key word (e.g., `alchemy` for the above entry) MUST NOT BE CHANGED.  This value is used to identify the translation entry.
- The key word `set_name` MUST NOT BE CHANGED, but the value after the `:` should be changed to the name of the set in the target language.
- The key word `text_icon` MUST NOT BE CHANGED, but the value after the `:` should be a one or two letter identifier to be used by the set if the set graphics are not displayed.  This is usually the first letter of the set name in the target language.
- Do not change any punctuation outside of the quotes `"`.  For example, brackets `{` or `}`, colons `:`, quotes `"` or commas `,`.


## Anatomy of bonuses_xx.json
Entries in this file represent Dominion bonuses. A typical entry looks like:

    "exclude": [
        "token",
        "Tokens"
    ],
    "include": [
        "Coins",
        "Coin",
        "Cards",
        "Card",
        "Buys",
        "Buy",
        "Actions",
        "Action",
        "<VP>"
    ]

The items in the `include` list are items that will be marked **bold** (i.e., `<b>..</b>`)
when found in the card text in the following format:

 `+# item_from_include_list`

as long as this is not followed by a item from the `exclude` list.
For example in English:
 `+2 Buys` will be made bold, but
 `+1 Action token` will not, since the key word token follows.

- Just replace the English terms with the terms used in the target language.
- Generally you should include the singular as well as the plural version of the term.
- English versions do not need to be duplicated, since they are used automatically.
- The key words `exclude` and `include` MUST NOT BE CHANGED.
- Do not change any punctuation outside of the quotes `"`.  For example, brackets `{` or `}`, colons `:`, quotes `"` or commas `,`.

## Anatomy of types_xx.json
Entries in this file represent Dominion card types.  A typical entry looks like:

    "Action": "Action in new language",

- The type key word (i.e., the `Action` for the above entry) MUST NOT BE CHANGED. This value is used to identify the translation entry.
- Do not change any punctuation outside of the quotes `"`.  For example, brackets `{` or `}`, colons `:`, quotes `"` or commas `,`.

## Anatomy of cards_xx.json
Entries in this file represent Dominion cards, and groups of cards.  A typical entry looks like:

    "Gold": {
        "description": "Worth 3 Coins.",
        "extra": "30 cards per game.",
        "name": "Gold"
    },

- The card key word (e.g., `Gold` for the above entry) MUST NOT BE CHANGED.  This value is used to identify the translation entry.
- The key word `name` MUST NOT BE CHANGED, but the value after the `:` should be changed to the name of the card in the target language.
- The key word `description` MUST NOT BE CHANGED, but the value after the `:` should be changed to the card text in the target language.
- The key word `extra` MUST NOT BE CHANGED, but the value after the `:` should be changed to any extra rules or explanations for the card in the target language.  If you purposely want no extra text, enter `""`.
- You can leave out/remove any of these keys in an entry while translating and they will be filled in with the English version
## Special Text
These character sequences have special meaning in the "description" and "extra" text:

- `<b>` ... `</b>` for **bold**
- `<i>` ... `</i>` for *italics*
- `<u>` ... `</u>` for underline
- `<tab>` and `<t>` and `\t` to add a tab (4 spaces)
- `<n>` and `\n` for a "hard new line"
- `<br>` and `<br/>` and `<br />` for a "soft new line"
- `<c>` and `<center>` add hard new line and center text until the next hard new line
- `<l>` and `<left>` add hard new line and left align text until the next hard new line
- `<r>` and `<right>` add hard new line and right align text until the next hard new line
- `<j>` and `<justify>` add hard new line and justify align text until the next hard new line
- `<line>` to add a hard new line, a centered dividing line, and a trailing hard new line

Hard new lines (`\n` and `<n>`), will reset the paragraph formatting back to the default.
Soft new lines will insert a new line, but will continue the current formatting.

The `description` will be default to "center" text.

The `extra` will default to "justify" text.

## Special Images
Special character sequences are recognized by the program to substitute graphics in the text.  These include:

- `<VP>` and ` VP ` for a Victory Point graphic
- `Potion` for a small Potion graphic
- `# Coin`  where # is a number 0 - 13, a question mark `?`, `_`, or the letters `empty` for a small coin graphic with the # on top
- `# Coins` where # is a number 0 - 13, a question mark `?`, `_`, or the letters `empty` for a small coin graphic with the # on top
- `# coin`  where # is a number 0 - 13, a question mark `?`, `_`, or the letters `empty` for a small coin graphic with the # on top
- `# coins` where # is a number 0 - 13, a question mark `?`, `_`, or the letters `empty` for a small coin graphic with the # on top
- `# Debt` where # is a number 0 - 13, for a small debt graphic with the # on top
- `# <*COIN*>` where # is a number 0 - 13, will produce a large coin graphic with the # on top
- `# <*VP*>` where # is a number, will produce a large Victory Point graphic with the # before it
- `# <*POTION*>` where # is a number, will produce a large Potion graphic with the # before it

For example:
- the text `1 coin` would produce a graphic of a coin with the number 1 on top.
- the text `empty coin` and `_ coin` would produce a graphic of only a coin.

IMPORTANT: To keep the special images, please do not translate any of the above Special character sequences into the target language.

## Style Guide

- If bonuses_xx.json for the target language is configured correctly, bonuses within the text will automatically be bolded.
  In English, it will not bold the text if it is followed by `token` or `Token`.  Example:

  `Choose one: +3 Cards; or +2 Actions.` will bold `+3 Cards` and `+2 Actions`.

- Bonuses should be listed in the following order:

  * `+ Cards`,
  * `+ Actions`,
  * `+ Buys`,
  * `+ Coins`,
  * `+ <VP>`

- When possible, bonuses should be listed vertically and centered.  Examples:

  * `+1 Card<br>+1 Action<br>+1 Buy<br>+1 Coin<br>+2 <VP><n>`
  * `+1 Card\n+1 Action\n+1 Buy\n+1 Coin\n+2 <VP>\n`

  The `description` field by default is centered. `<br>`, `<n>`, and `\n` will all provide new lines.

- If a Dividers/Tab has more than one card explanation, if space permits, try to mimic a stand alone Dividers/Tab in the overall format. Example from "Settlers - Bustling Village":

    `<left><u>Settlers</u>:<n>+1 Card<br>+1 Action<n>Look through your discard pile.
    You may reveal a Copper from it and put it into your hand.<n>
    <left><u>Bustling Village</u>:<n><center>+1 Card<br>+3 Actions<n>
    Look through your discard pile. You may reveal a Settlers from it and put it into your hand.`
