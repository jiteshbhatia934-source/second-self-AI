---
id: '1-program-ka-purpose-kya-hai-2'
raw_id: '1-program-ka-purpose-kya-hai-2'
para: 'Projects'
tags:
  - 'include'
summary: '1.'
title: '1. Program ka Purpose kya hai?'
created_at: '2026-08-01T02:31:09.791066+00:00'
classified_at: '2026-08-01T02:31:09.791066+00:00'
embedding_version: 'all-MiniLM-L6-v2'
---
1. Program ka Purpose kya hai?

Ye program ek calculator jaisa hai jisme user menu se choice karega:

(1) Addition

(2) Subtraction

(3) Multiplication

(4) Division

(5) Remainder

(0) Exit

Aur fir do numbers dalne ke baad uska result print hoga.

2. Har line ka Matlab
#include <stdio.h>

Ye ek library hai jisme input/output functions hote hain jaise printf aur scanf.

printf → output show karne ke liye

scanf → input lene ke liye

#include <stdlib.h>

Is library ka use humne exit(0) ke liye kiya hai.

exit(0); ka matlab hai program turant band kar do.

int main()

Ye har C program ka starting point hota hai. Jab program run hota hai, sabse pehle main() function hi start hota hai.

Humne int isliye likha hai kyunki program last me ek integer return karta hai (return 0;).

3. Variables ka kaam
int a, b, res, ch;


a aur b → do numbers jo user input karega.

res → calculation ka result yahan store hoga.

ch → user ka choice number (menu se jo bhi select karega).

4. Menu Print karna
printf("\t(1)Addition");
printf("\n\t(2)Subtraction");
...


Yeh bas screen par options dikhane ke liye likha hai.
\t = tab space (thoda andar se likhne ke liye).
\n = new line (neeche line me jane ke liye).

5. User se Choice Lena
scanf("%d", &ch);


%d ka matlab → integer input.

&ch matlab → input jo user dalega, voh ch variable me store hoga.

6. Condition Check karna
if (ch >= 0 && ch <= 5)


Iska matlab → agar choice 0 se 5 ke beech hai tabhi aage chalega.

&& ka matlab hai AND (dono condition true honi chahiye).

7. Do Numbers Input Lena
scanf("%d %d", &a, &b);


User ek saath 2 numbers dal sakta hai (space ya enter karke).

Pehla number a me store hoga

Dusra number b me

8. Switch Statement

Switch ek tarah ka shortcut hai multiple if else ke liye.

switch (ch)
{
    case 1: res = a + b;
            printf("Addition = %d", res);
            break;


Agar ch = 1 → Addition hoga.

Agar ch = 2 → Subtraction hoga.

Agar ch = 3 → Multiplication hoga.

Agar ch = 4 → Division hoga.

Agar ch = 5 → Remainder hoga.

Agar ch = 0 → program exit ho jayega.

👉 break; ka matlab hai switch se bahar aa jana. Agar break na likho toh neeche ke cases bhi chalne lagenge.

9. Return Statement
return 0;


Ye batata hai ki program successfully end ho gaya.

10. Example Execution
*********************
MENU
*********************
(1)Addition
(2)Subtraction
(3)Multiplication
(4)Division
(5)Remainder
(0)Exit
*********************
Enter your choice: 1
Enter two numbers: 5 7
Addition = 12


## Related

- [[1-program-ka-purpose-kya-hai-1]]
- [[1-program-ka-purpose-kya-hai]]

