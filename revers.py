num = int(input("Enter a number: "))
reverse = 0

while num < 0:   
    digit = num % 10
    reverse = reverse + digit  
    num = num / 10   

print("Reversed number:", num)  