@echo off
echo Preparing to push your code to GitHub...
echo.

git init
git add .
git commit -m "Fixed startup bugs and added hosting configurations"
git branch -M main

:: Remote origin add kar rahe hain
git remote remove origin 2>nul
git remote add origin https://github.com/KrishParashar37/Flight-booking-web-site-.git

echo.
echo Pehle remote repository se changes pull kar rahe hain...
git pull origin main --allow-unrelated-histories --no-edit

echo.
echo Pushing code to GitHub...
git push -u origin main

echo.
echo Upload Complete! You can close this window now.
pause
