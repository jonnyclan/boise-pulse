@echo off
cd /d "C:\Users\jonny\Desktop\Dunzo\morning-edition"
echo ============================================
echo  Boise Pulse - Friday Newsletter
echo ============================================
echo.
python pre_publish_check.py --preview 2>&1
echo.
echo ============================================
echo  DONE. Press any key to close.
echo ============================================
pause
