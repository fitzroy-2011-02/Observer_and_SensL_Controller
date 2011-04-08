$(document).ready(function() {
	// generate tabs
	$(function() {
		$( "#tabs" ).tabs();
		$( "#showResultBut" ).button();
		$( "#execCMD" ).button();
	});

	// just allow numbers as input to textfields 		
	$(".inputEle").numeric({allow:"."});

	// set some nice corners
	$("#mainDIV").corner("5px");
	$("#connectScreen").corner("5px");
	$("#elementDIV").corner("5px");
	$("#startDIV").corner("5px");
	$(".eleLabel").corner("3px");
	$(".dirBut").corner("3px");
	$("#customCMD").corner("5px");
	$("#showResult").corner("5px");
	$("#sensorConfigBackDIV").corner("5px");
	$("#startSensLBUT").corner("5px");
	$("#mikDIV").corner("5px");
	
	$("#startSensL").corner("5px");
	$("#startSensLZStapel").corner("5px");
	$("#startSensLZStapelBUT").corner("5px");
	$(".eleLabelZStapel").corner("3px");
	
	// set default input values
	$("#inputFrequenz").val("100");
	$("#inputFileName").val("testLauf");
	
	$("#inputVel").val("6.43");
	$("#inputDist").val("700");
	$("#inputCycle").val("1");
	
	$("#startSensLFrequenz").val("100");
	$("#startSensLFileName").val("testSensor");
	
	$("#startSensLZStapelExpTime").val("100");
	$("#startSensLZStapelExpCount").val("10");
	$("#startSensLZStapelStepCount").val("1");
	$("#startSensLZStapelStepDist").val("100");
	
	
	/* ----------------------------------
	call python: connect to mikroscope and check Sensor availability
	-----------------------------------*/
	$("#connectScreen").bind('click', function()
	{
		$.post('/cCOM',
			{ "comPort":"0" },
			function(res) {
				// res.resMic = 1;
				// res.resSAPD = 1; 
				if( (res.resMic != "0") && (res.resSAPD != "0" ))
				{
					// now show the controll elements
					writeSring = "Connected to COM Port: 1 and Sensor available"; 
					writeLog(writeSring, "output");
					$("#connectScreen").fadeOut();
				}
				else
				{
					// error occured and one result is 0
					// print results
					errorCode = "Mikroskop result: " + res.resMic + "<br> Sensor result: " + res.resSAPD;
					$("#connectString").html(errorCode);
					setTimeout(function(){$("#connectString").html("CONNECT");}, 3000);
				}
			},
			'json'
		);
	});
	// ---------------------------------------
	
	/* ----------------------------------
	call python: to start movement
	----------------------------------- */
	$("#startDIV").bind('click', function()
	{
		$("#startDIV").toggleClass("startMove");
		$("#startDIV").toggleClass("stopMove");

		if($("#startDIV").hasClass("startMove"))
		{     
			// set DIV content
			$("#startDIV").html("STOP");

			// first collect data we need to send
			vel = $("#inputVel").val();
			dist = $("#inputDist").val();
			// convert distance to micrometer
			dist = dist * 10;
			cycle = $("#inputCycle").val();
			
			if ( $("#dirHoriz").hasClass("butSelected") ){
					dirString = "X=";}
			else{ dirString = "Y="; }
			
			// now make the calls we need
			// 1. get old velocity - to reset after movement
			// 2. set new velocity
			// 3. start sensor record if selected
			// 4. make move(s)
			
			// 1. get old velocity		
			writeLog("S X? Y?", "input");
			$.post('/callCMD',
					{ "callString": "S X? Y?" },
					function(res) {
							oldVelRes = "S X? Y? returns: " + res.res;
							writeLog(oldVelRes, "output");
							// ersten beiden Zeichen weglassen, speichern um
							// spaeter zurueckzusetzen
							oldVelCall = oldVelRes.slice(2);               
					},
					'json'
			);
						
			// 2. set new velocity
			newVelString = "S X=" + vel + " Y=" + vel;
			writeLog( newVelString, "input" );
			$.post('/callCMD',
					{ "callString": newVelString },
					function(res) {
							newVelRes = newVelString + " returns: " + res.res;
							writeLog(newVelRes, "output");              
					},
					'json'
			);
			
			// 3. start sensor record if selected
			if( $("#sensLSelectBUT_ON").hasClass("sensLSelectBUT_check") )
			{
				// get filename and rate
				rate = 	$("#inputFrequenz").val();
				
				writeLog( "Start SensL APD", "input" );
				$.post('/startSensLAPD',
							{ "expTime": rate},
							function(res)
							{
								logLine = "Start SensL APD returns: " + res.res;
								writeLog(logLine, "output" );
							},
							'json'
				);
			}

			// make move(s)        
			vorzeichen = Math.pow(-1,cycle);
			vorzeichen += '';
			if(vorzeichen == '1'){vorzeichen='';}
			else{vorzeichen = '-';}
			cycle--;
			moveString = "R " + dirString + vorzeichen + dist;
			writeLog( moveString, "input" );
			$.post('/callCMD',
					{ "callString": moveString },
					function(res) {
						logLine = moveString + " returns: " + res.res;
						writeLog( logLine, "output");
						recursiveStatusCall();
					},
					'json'
			);

		}
		else
		{
			// set DIV content
			$("#startDIV").html("GO");
			$("#startDIV").toggleClass("startMove");
			$("#startDIV").toggleClass("stopMove");	

			// stop move and save data
			stopString = "HALT";
			writeLog( stopString, "input");
			$.post('/callCMD',
						{ "callString": stopString },
						function(res) {
								logLine = stopString + " returns: " + res.res;
								writeLog(logLine, "output");

                
                                if( $("#sensLSelectBUT_ON").hasClass("sensLSelectBUT_check") )
                                {								
                                    // save data, generate HTML Page and reset old velocity
                                    fileName = $("#inputFileName").val();
                    
                                    writeLog( "Stop SensL APD", "input" );
                                    $.post('/stopSensLAPD',
                                        {"fileName": fileName},
                                        function(res)
                                        {
                                            logLine = "Stop SensL APD returns: " + res.res;
                                            writeLog( logLine , "output" );
                                            if( res.error == "0" ){
                                                htmlPageURL = res.res;
                                                window.open( htmlPageURL,'_newtab' );
                                            }
                                        },
                                        'json'
                                    );
								}
                                
								writeLog( oldVelCall, "input" );
								$.post('/callCMD',
										{ "callString": oldVelCall },
										function(res) {
												logLine = oldVelCall + " returns: " + res.res;
												writeLog(logLine, "output");              
										},
										'json'
								);            
							
						},
						'json'
			);
			
		}        
	});
	// ---------------------------------------
	
	/* ----------------------------------
	call python: to exec custom command
	----------------------------------- */	
	$("#execCMD").bind('click', function()
	{
		// get cmd string from input field
		cmdString = $("#inputCMD").val();
		writeLog(cmdString, "input");
		$.post('/callCMD',
            { "callString": cmdString },
            function(res) {
							logLine = cmdString + " returns: " + res.res;
							writeLog( logLine, "output" );
            },
            'json'
        );
	});
	// ---------------------------------------
	
	/* ------------------------------------------------------
	call python: observe the movement, check if move finished
	------------------------------------------------------ */
	function recursiveMoveCall()
	{
		if(cycle > 0)
		{
			vorzeichen = Math.pow(-1,cycle);
			vorzeichen += '';
			if(vorzeichen == '1'){vorzeichen='';}
			else{vorzeichen = '-';}
			
			moveString = "R " + dirString + vorzeichen + dist;
			writeLog( moveString );
			$.post('/callCMD',
							{ "callString": moveString },
							function(res) {
								writeLog( res.res, "output");
								cycle--;
								recursiveStatusCall();
							},
							'json'
			);
		}
		else
		{
			// reset DIV content
			$("#startDIV").html("GO");
    		$("#startDIV").toggleClass("startMove");
            $("#startDIV").toggleClass("stopMove");            

            if( $("#sensLSelectBUT_ON").hasClass("sensLSelectBUT_check") )
            {

                //all moves done, now reset velocity and stop sensor
                fileName = $("#inputFileName").val();
                
                writeLog( "Stop SensL APD", "input" );
                $.post('/stopSensLAPD',
                    {"fileName": fileName},
                    function(res)
                    {
                        logLine = "Stop SensL APD returns: " + res.res;
                        writeLog( logLine , "output" );
                        if( res.error == "0" ){
                            htmlPageURL = res.res;
                            window.open( htmlPageURL,'_newtab' );
                        }
                    },
                    'json'
                );
            }
                
			
			writeLog( oldVelCall, "input" );
			$.post('/callCMD',
					{ "callString": oldVelCall },
					function(res) {
						logLine = oldVelCall + " returns: " + res.res;
						writeLog(logLine, "output");             
					},
					'json'
			);
			
		}
	};
	
	function recursiveStatusCall()
	{
		$.post('/callCMD',
            { "callString": "STATUS" },
            function(res) {
            	//writeLog( res.res, "output" );
            	if( res.res == "N" ){
                	recursiveMoveCall();
            	}
            	else{
            		recursiveStatusCall();
            	}
            },
            'json'
    );
	};
	// -----------------------------------------------------------
	
	// select horizontal or vertical movement 
	$(".dirBut").bind('click', function()
	{
		$(".dirBut").toggleClass("butSelected");
	});
	
	// select if we want to use the sensL Sensor or not
		$(".sensLSelectBUT").bind('click', function()
	{
		if($(this).hasClass("sensLSelectBUT_check")){
			return true;
		}
		else
		{
			$("#sensLSelectBUT_ON").toggleClass("sensLSelectBUT_check");
			$("#sensLSelectBUT_OFF").toggleClass("sensLSelectBUT_check");
			return true;
		}
	});
	
	// write to textarea DIV - log, by adding new divs with
	// corresponding text
	function writeLog( textString, inORout )
	{
		var newLine = $("<div/>");
		
		// get current time stamp :)
		var dateVar = new Date();
		var timeStamp_hours = dateVar.getHours();
		var timeStamp_minutes = dateVar.getMinutes();
		var timeStamp_seconds = dateVar.getSeconds();
		
		if(inORout == "output"){
			newLine.html(" >>> ");
		}
		if(inORout == "input"){
			newLine.html(" <<< ");
		}
				
		timeStamp = timeStamp_hours + ":" + timeStamp_minutes + ":" + timeStamp_seconds;
		
		newLineTxt = timeStamp + newLine.html() + textString;
		newLine.html(newLineTxt);
		$("#logArea").append( newLine );
	};
	
	/* ------------------------------------------------------
	call python: generate html page with data visualization
	------------------------------------------------------ */
	$("#showResultBut").bind('click', function()
	{
		fileName = $("#inputPlotFileName").val();
		writeLog( "Generate HTML from data: " + fileName, "input" );
		$.post('/showResult',
            {"fileName": fileName},
            function(res)
						{
							writeLog( "Generate HTML from data result: " + res.res, "output" );
							htmlPageURL = res.res;
							window.open( htmlPageURL,'_newtab' );
            },
            'json'
        );
	});
	// -------------------------------------------------------
	
	/* ------------------------------------------------------
	call python: 	start/stop sensL APD Sensor and
								generate a plot - no microscop action
	------------------------------------------------------ */
	$("#startSensLBUT").bind('click', function()
	{
		// stop movement
		if( $("#startSensLBUT").hasClass("startSensLBUT_select") )
		{
			// change ext of the button
			$("#startSensLBUT").toggleClass("startSensLBUT_select");
			$("#startSensLBUT").html("START");
			
			fileName = $("#startSensLFileName").val();
			
			writeLog( "Stop SensL APD", "input" );
			$.post('/stopSensLAPD',
				{"fileName": fileName},
				function(res)
				{
					logLine = "Stop SensL APD returns: " + res.res;
					writeLog( logLine , "output" );
					if( res.error == "0" ){
						htmlPageURL = res.res;
						window.open( htmlPageURL,'_newtab' );
					}
				},
				'json'
            );
			
		}
		// start movement
		else
		{
			// change text of the button
			$("#startSensLBUT").toggleClass("startSensLBUT_select");
			$("#startSensLBUT").html("STOP");
			
			// get exposure time
			expTime = 	$("#startSensLFrequenz").val();
			
			writeLog( "Start SensL APD", "input" );
			$.post('/startSensLAPD',
						{ "expTime": expTime},
						function(res)
						{
							logLine = "Start SensL APD returns: " + res.res;
							writeLog(logLine, "output" );
						},
						'json'
			);
		}
		
		// change color and text of the button
		
		/*
		$.post('/showResult',
            false,
            function(res)
						{
							htmlPageURL = res.res;
							window.open( htmlPageURL,'_newtab' );
            },
            'json'
        );
		*/
	});
	
	// -------------------------------------------------------
	
	/* ------------------------------------------------------
	call python: 	move z axes to find focus position and
								generate plot
	------------------------------------------------------ */
	$("#startSensLZStapelBUT").bind("click", function()
	{
		
		// stop search
		if( $("#startSensLZStapelBUT").hasClass("startSensLZStapelBUT_select") )
		{
			
		}
		// start search
		else
		{
			// change text of the button
			$("#startSensLZStapelBUT").toggleClass("startSensLZStapelBUT_select");
			$("#startSensLZStapelBUT").html("STOP");
			
			// get parameter
			
			zStepCount = 	$("#startSensLZStapelStepCount").val();
			zStepDist = 	$("#startSensLZStapelStepDist").val();
			expTime = 		$("#startSensLZStapelExpTime").val();
			expCount = 		$("#startSensLZStapelExpCount").val();
			
			writeLog( "Start search Z focus", "input" );
			$.post('/startSensLZStapel',
						{	"zcount":	zStepCount,
							"zdist": 	zStepDist,
							"expTime":	expTime,
							"expCount":	expCount
						},							
						function(res)
						{
							logLine = "Start search Z focus returns: " + res.res;
              writeLog( logLine , "output" );
							if( res.error == "0" )
							{
									htmlPageURL = res.res;
									window.open( htmlPageURL,'_newtab' )
							}
						},
						'json'
			);
            // change ext of the button
			$("#startSensLZStapelBUT").toggleClass("startSensLZStapelBUT_select");
			$("#startSensLZStapelBUT").html("START");
		}
		
		
		
		
	});
	
	// -------------------------------------------------------
	
});	