#include <Stepper.h>

// Define the number of steps per revolution for the stepper motor
const int stepsPerRevolution = 2048;

// Initialize stepper motor
// Pins entered in sequence IN1-IN3-IN2-IN4 for proper step sequence
Stepper myStepper = Stepper(stepsPerRevolution, 8, 10, 9, 11);

// Define pins for the ultrasonic sensor
int trigPin = 7;
int echoPin = 6;

// Define variables
float steps, angle, currentPosition;
float duration, distance, dist;
float speedOfSound = 0.0345;

bool running = false;

String msg;

// Define the number of scans per revolution
int scansPerRevolution = 100;

void setup() {
  // Initialize sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Set the speed of the stepper motor to 5 RPM
  myStepper.setSpeed(5);

  // Initialize serial communication at 9600 bits per second
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    msg = Serial.readString();

    // If the message is "start", start the scanning process
    if (msg == "start") {
      running = true;
      currentPosition = 0;

      while (running) {
        // Loop through the number of scans per revolution
        for (int i = 0; i <= scansPerRevolution; i++) {
          if (checkIfStop() || !running) {
            returnToInitialPosition();
            running = false;
          } else {
            oneIteration(i);
          }
        }
        returnToInitialPosition();
      }
    }

    delay(100);
  }
}

// Function to return the stepper motor to its initial position
void returnToInitialPosition() {
  steps = -currentPosition;
  currentPosition = 0;

  moveSteps();
}

// Function to check if the stop command has been received
bool checkIfStop() {
  return Serial.available() > 0 && Serial.readString() == "stop";
}

// Function to perform one iteration of the scanning process
void oneIteration(int i) {
  steps = (float)stepsPerRevolution / (float)scansPerRevolution;
  angle = steps * (float)i / (float)stepsPerRevolution * (float)360.0;

  currentPosition += steps;

  moveSteps();

  // Print results to the serial monitor
  Serial.print(angle);
  Serial.print(",");
  Serial.print(calculateDistance());
  Serial.print(",");
  Serial.print(currentPosition);

  Serial.println();

  delay(100);
}

// Function to move the stepper motor by a certain number of steps
void moveSteps() {
  myStepper.step(steps);
}

// Function to get the distance from the ultrasonic sensor
float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);

  return (duration * speedOfSound) / 2;
}

// Function to handle distance calculation
float calculateDistance() {
  distance = getDistance();

  // If the distance is out of range, get the distance again
  if (0 < distance > 400) {
    distance = getDistance();
  }

  return distance;
}
