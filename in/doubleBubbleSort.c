/*
    doubleBuddleSort.c
    双端冒泡排序
*/
#include <stdio.h>

int main() {
    int arr[65535];
    int n = 0;
    char c;
    while (1) {
        scanf("%d", &arr[n]);
        n = n + 1;
        scanf("%c", &c);
        // c = getchar();
        if (c != ',') {
            break;
        }
    }

    int l = 0;
    int r = n - 1;
    int p = 0;
    while (l < r) {
        p = l;
        while (p < r) {
            if (arr[p] > arr[p + 1]) {
                int temp = arr[p];
                arr[p] = arr[p + 1];
                arr[p + 1] = temp;
            }
            p = p + 1;
        }
        r = r - 1;

        p = r;
        while (p > l) {
            if (arr[p] < arr[p - 1]) {
                int temp = arr[p];
                arr[p] = arr[p - 1];
                arr[p - 1] = temp;
            }
            p = p - 1;
        }
        l = l + 1;
    }

    p = 0;
    while (p < n) {
        printf("%d", arr[p]);
        if (p != n - 1) {
            printf(",");
        }
        p = p + 1;
    }
    return 0;
}
