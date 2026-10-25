# Email Search Guide

## Overview

The Email Search utility searches existing EML email files using configurable JSON search criteria.

You can run an individual search or run all configured searches sequentially.

The utility does not require selecting a PST file or converting PST files during a search.

## Main Configuration

Search configurations are registered in `EmailConfig.json` using the `search_configs` list.

Example:

```json
"search_configs": [
  "~/Documents/email/search/InvoiceSearch.json",
  "~/Documents/email/search/AddressSearch.json",
  "~/Documents/email/search/ProjectSearch.json"
]
```

The `locations.search_readme_path` setting points to this guide, displayed by **View Email Search Help** (for example, `email/SearchReadMe.md`).

## Search Configuration Format

Each search configuration defines its own search location, results location, matching mode and keywords.

```json
{
  "search_location": "~/Documents/TestingToolsData/email/eml",
  "results_location": "~/Documents/TestingToolsData/email/search_results/invoices",
  "match": "any",
  "criteria": {
    "from": [],
    "to": [],
    "subject": ["invoice", "receipt"],
    "body": ["amount due", "payment received"]
  }
}
```

## Configuration Fields

- **search_location:** Directory containing EML files. All subdirectories are searched recursively.
- **results_location:** Directory where matching EML files are copied.
- **match:** Determines how populated criteria fields are combined.
- **criteria.from:** Keywords matched against sender information.
- **criteria.to:** Keywords matched against recipient information.
- **criteria.subject:** Keywords matched against email subjects.
- **criteria.body:** Keywords matched against email body text.

## Matching Rules

Searches are case-insensitive.

**any:** An email matches when at least one keyword in any populated field is found.

**all:** An email matches when at least one keyword is found in every populated field.

Empty keyword lists are ignored.

## Running Searches

Select **Search emails** from the Email utility menu.

Choose a numbered search configuration to run one search, or select **All Search Configurations** to execute every registered configuration sequentially.

Each search uses its own results directory and saves matching emails there. Selecting **All Search Configurations** combines the results into one paginated table.

## Viewing Saved Results

Select **View Search Results** from the Email utility menu.

Choose one search configuration or **All Search Configurations**. This action loads previously saved EML files from each selected configuration's `results_location` without rerunning the search. Selecting all configurations combines their saved results into one paginated table.

When viewing saved results, the **Matched** column identifies the originating search configuration by its filename without the `.json` extension. It does not show matched criteria fields in this view.

## Search Results

Matching emails are copied as complete EML files, preserving their relative subfolder structure.

Results are displayed in a paginated table with:

- Number
- Date
- From
- Subject
- Matched (matched fields for a new search; originating configuration for saved results)

Enter an email number to view its details and body.

Use `N` for the next page, `P` for the previous page, or `Q` to exit.

## Overwriting Results

If a results directory already exists, the utility asks for confirmation before deleting and recreating it.

Answering `y` removes the existing contents of that results directory.

Answering `n` cancels that search without deleting existing files.

## Limitations

Body searches use the existing email body extraction helper. HTML-only messages and additional text sections in multipart emails may not be fully searchable.

Searches operate on EML files already present on disk, not directly on PST files.
