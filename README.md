This is a python module to help calculate the available Δv for any spaceship based on its dry mass, propellant mass, and specific impulse.

I'll add instructions if anyone is interested!

Todo:  
-finish Ship.burn.  
-kN?? unit suffixes everywhere??  
-make error detection in _burn proportional.  
-add validate method to engine.  
-make it so that Ship.burn can run until a speed is reached or a resource runs out.  
-make a+b=c solver and use it for working on ship init inputs.  
-add tests.  
Done:  
-use the same format for resources in all arguments.  
-add burn time calculations.  
-add engine block.  
-split burn into burn and _burn.  
-add input validation for ship __init__.  
-make it possible for Ship to be initialized using known total mass instead of known dry mass.  
-make it possible for Ship to be initialized with units instead of tons for resources.  