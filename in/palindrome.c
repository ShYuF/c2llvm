/*
    palindrome.c
    回文串检测
*/
#include <stdio.h>

int main() {
    char str[65535];

    gets(str);
    int len = 0;

    while (str[len] != '\0' && str[len] != '\n' && str[len] != '\r') {
        len = len + 1;
    }

    int p = 0;
    int flag = 1;
    while (p < len / 2 && flag == 1) {
        if (str[p] != str[len - p - 1]) {
            flag = 0;
        }
        p = p + 1;
    }

    if (flag == 1) {
        printf("True");
    }
    else {
        printf("False");
    }

    return 0;
}