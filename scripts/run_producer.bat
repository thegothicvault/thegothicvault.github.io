@echo off
REM Stiletto Vault auto-producer — drains production_queue.json into ad candidates
REM on Telegram. Wired to a daily Windows Task (~10:00). Stops at ads; video only
REM runs after Ofer picks in Telegram. Logs to scripts\producer.log.
cd /d E:\PROJECTS\thegothicvault
echo ================================================================ >> scripts\producer.log
echo producer run: %date% %time% >> scripts\producer.log
"C:\Users\ofera\.local\bin\claude.exe" -p "Read scripts/produce_queue.md and follow it exactly to drain the Stiletto production queue. Stop at the ads and push them to Telegram; never generate video." --dangerously-skip-permissions >> scripts\producer.log 2>&1
echo producer done: %date% %time% >> scripts\producer.log
