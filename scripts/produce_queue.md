# Stiletto Vault — Auto-Producer (queue runner)

You are running headless. Task: drain the production queue by turning each approved
lead into 4 ad candidates and pushing them to Telegram for Ofer's A/B/C/D pick.
**Stop at the ads. Never generate video** — the video (the expensive step) runs
only after Ofer picks an ad, in a separate flow.

## Steps

1. Read `E:/PROJECTS/thegothicvault/data/production_queue.json`.
   If it is missing, empty, or no entry has `status == "approved"` → print
   "queue empty — nothing to produce" and STOP. Do nothing else.

2. For EACH entry with `status == "approved"` (process at most 5 per run):

   a. slug = run `py -3 E:/PROJECTS/thegothicvault/scripts/space_runner.py` is not
      needed — derive it the same way: AliExpress `/item/<id>` → `<title-slug>-<id>`.
      The folder is the entry's `local_asset` basename; use that slug.

   b. Upload the source: `mcp__magnific__creations_upload_image(url = entry.image_url)`
      → note the returned `identifier` (SOURCE_ID).

   c. Point the Space at it. The Input panel (1b00f6ed) holds MULTIPLE reference
      Creation nodes, ALL wired into both the concept builder (5ec8e287) and the
      campaign image generator (93b85932). They must ALL hold the SAME shoe, or the
      generator blends several shoes and invents a wrong one (this was the
      consistency bug). Current reference Creation nodes:
        0114e22a-6027-490e-aeca-b1b428d8ca91
        02abd82d-b225-4a27-abeb-cf3b7912cfd0
        0668d990-b1a7-43c1-93db-ef221fe6666f
        7b24da13-2075-4f2b-9884-8f10fc769810
      (Re-read them first with spaces_get_nodes — the ids can change if the board is
      rearranged; the correct set is every `creation` child of panel 1b00f6ed that
      feeds 5ec8e287/93b85932.)
      For EACH of those nodes:
      `mcp__magnific__spaces_edit(spaceId="a2796464-3570-4e02-aa77-65f3f4322d9f",
        selectedElementIds=["<that node id>"],
        query="Replace the image held by this Creation node with uploaded creation
        <SOURCE_ID> — the new heel product photo. Do not change any wiring.")`
      Poll `spaces_edit_status` until `allTerminal`. Verify with `spaces_get_nodes`
      that EVERY one of those nodes now has `creationIdentifier == SOURCE_ID`.
      Only when all match, proceed — otherwise the shoe will be inconsistent.

   d. Run the ads chain (NOT the video):
      `mcp__magnific__spaces_run(spaceId="a2796464-3570-4e02-aa77-65f3f4322d9f",
        startNodeId="5ec8e287-6633-44a9-bcaf-2562c656728e", mode="downstream")`
      Poll `spaces_run_status` until `allTerminal`. Collect the 4 creation ids from
      node `93b85932-6752-4bfa-a801-28fd3c0c097c`.

   e. `mcp__magnific__creations_wait` on the 4 ids → 4 render URLs.

   f. Download to `E:/PROJECTS/thegothicvault/GELEM/<slug>/ad_A.jpg … ad_D.jpg`
      with curl (also copy source.jpg there). Order A,B,C,D = the 4 ids in order.

   g. Send for the pick:
      `py -3 E:/PROJECTS/thegothicvault/scripts/orchestrator.py send <slug>`

   h. Set that entry's `status = "awaiting_choice"` in production_queue.json and save.

3. Print a one-line summary: how many leads produced, how many skipped, any errors.

## Guardrails
- Cap: 5 leads per run. If more are approved, leave the rest for the next run.
- Never touch entries whose status is not `approved`.
- Never run the video generator node here.
- If any single lead errors, log it, leave its status as `approved`, and continue
  to the next — do not abort the whole run.
