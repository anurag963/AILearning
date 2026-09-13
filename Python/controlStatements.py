# if, if else, Nested if, if-elif-else


num1= 1
num2= 2 
if(num1>num2):
    print(str(num1)+" is greater than "+str(num2))
elif(num1==num2):
    print(str(num1)+" is equal to "+str(num2))
else:
    print(str(num2)+" is greater than "+str(num1))



#day = int(input("Enter day in digit\n"))
day= "Tuesday"
match day:
    case 1:
        print("Monday")
    case 2:
        print("Tuesday")
    case 3:
        print("Wednesday")
    case 4:
        print("Thursday")
    case 5:
        print("Friday")
    case 6:
        print("Saturday")
    case 7:
        print("Sunday")
    case _:
        print("Invalid input")



# Loops
# for loop, while loop, nested loop, break, continue, pass
# pass- pass is for the placeholder in the loop, it does nothing but can be used to avoid error in the loop

str1= "Hello World"
for i in str1:
    print(i)



for i in range(5):
    print(i)
else:
    print("Loop completed")

