//HC-SR04 Ultrasonic distance sensor module

//Mark Benson

//23/07/2013

//Creative Commons non commercial

difference()
{
	union()
	{
		color("DARKBLUE")cube([45,20,1.2]);
		translate([16/2+1,18/2+1,1.3]) ultrasonicSensor();
		translate([16/2+27+1,18/2+1,1.3]) ultrasonicSensor();
		color("SILVER")translate([45/2-3.25,20-4,1.3]) xtal();
		translate([(45/2)-((2.45*4)/2)+0.6,2,-0.2]) rotate([180,0,0]) headerPin(4);
	}

	union()
	{
		color("DARKBLUE") translate([2.5,2.5,-1]) cylinder(r=2/2, h=3, $fn=50);
		color("DARKBLUE") translate([2.5+40,2.5+15,-1]) cylinder(r=2/2, h=3, $fn=50);
	}
}

module ultrasonicSensor()
{
	union()
	{
		//Sensor body
		color("SILVER")
		difference()
		{
			//Body
			translate([0,0,0]) cylinder(r=16/2, h=13.8, $fn=50);
			//Hole in body
			translate([0,0,0]) cylinder(r=12.5/2, h=14, $fn=50);
		}

		//Insert to indicate mesh
		color("GREY") translate([0,0,0]) cylinder(r=12.5/2, h=13, $fn=50);
	}
}

//ultrasonicSensor(); 

module xtal()
{
	//Xtal maximum dimensions for checking model
	//color("red")translate([0,0,-1]) cube([11.5,4.65,1]);
	//color("red")translate([(11.54-10.3)/2,(4.65-3.8)/2,0]) cube([10.3,3.8,3.56]);
	
	union()
	{
		//Base
		hull()
		{
			translate([0,0,0]) cylinder(r=4.65/2, h=0.4, $fn=50);
			translate([6.5,0,0]) cylinder(r=4.65/2, h=0.4, $fn=50);
		}
	
		//Body
		hull()
		{
			translate([0,0,0]) cylinder(r=3.7/2, h=3.56, $fn=50);
			translate([6.5,0,0]) cylinder(r=3.7/2, h=3.56, $fn=50);
		}
	}
}

module headerPin(numberOfPins)
{
	for (i = [0:numberOfPins-1])
	{
		color("GOLD") translate([(i*2.54),0,-2]) cube([0.5,0.5,8]);
		color("BLACK") translate([(i*2.54-2.54/2+0.25),-2.54/2+0.25,0]) cube([2.54,2.54,1]);
	}
}

//headerPin(4);

