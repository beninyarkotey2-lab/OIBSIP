while True:
   try:
       weight = float(input("Enter your weight in kilograms: "))
   except ValueError:
       print("Please enter a value/number.")
       continue
   if weight <= 0:
       print("Weight must be greater than zero.")
       continue
   break
while True:   
   try:
       height = float(input("Enter your height in metres:  "))
   except ValueError:
        print("Please enter a value/number.")
        continue
   if height <= 0:
        print("Height must be greater than 0.")   
        continue
   break
BMI = weight / (height ** 2)
print(f"{BMI:.2f}") 
if BMI < 18.5:
   print("category = Underweight")
elif BMI < 25:
   print("category = Normal")
elif BMI < 30:
    print("category = Overweight")
else:
    print("category = Obese")
    
