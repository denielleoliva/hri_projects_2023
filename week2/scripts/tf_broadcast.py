#!/usr/bin/env python3  
import rospy

# Because of transformations
import tf_conversions

import tf2_ros
import geometry_msgs.msg
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
import math
from people_msgs.msg import PositionMeasurementArray
from tf.transformations import euler_from_quaternion
from math import atan2
from nav_msgs.msg import Odometry

msg_twist=Twist()
linearx=0
angularz=0

theta=0
x=0
y=0

isBlocked=True
foundLegs=False
odomData=None

goal=Point()

def localRad(data):
    global odomData, theta

    x = data.pose.pose.position.x
    y = data.pose.pose.position.y

    yaw = data.pose.pose.orientation

    (roll, pitch, theta) = euler_from_quaternion([yaw.x, yaw.y, yaw.z, yaw.w])

# def avoid_follow(dat):
#     global isBlocked, linearx, angularz, msg_twist, foundLegs

#     range={
#         "right" : min(min(dat.ranges[0:239]) , 2),
#         "center" : min(min(dat.ranges[240:479]) , 2),
#         "left" : min(min(dat.ranges[480:719]) , 2)
#     }

#     if ( range["right"] >1  and range["center"] > 1 and range["left"] >1 and foundLegs):
#         isBlocked=False
#         linearx=0.4
#         angularz=0
#         print("front free")
#     elif ( range["right"] > 1  and range["center"] < 1 and range["left"] > 1 ):
#         isBlocked=True
#         linearx=0
#         angularz=-0.5
#         print("front wall")
#     elif ( range["right"] < 1  and range["center"] > 1 and range["left"] > 1 ):
#         isBlocked=True
#         linearx=0
#         angularz=0.5
#         print("right wall")
#     elif ( range["right"] > 1  and range["center"] > 1 and range["left"] < 1 ):
#         isBlocked=True
#         linearx=0
#         angularz=-0.5
#         print("left wall")

#     msg_twist.linear.x=linearx
#     msg_twist.angular.z=angularz
#     pub.publish(msg_twist)


def handle_leggies(msg):
    global msg_twist, goal
    br = tf2_ros.TransformBroadcaster()
    t = geometry_msgs.msg.TransformStamped()

    t.header.stamp = rospy.Time.now()
    t.header.frame_id = "odom"
    t.child_frame_id = "legs"

    if len(msg.people) == 0:
        print("no leggies")
        return None


    t.transform.translation.x = msg.people[0].pos.x
    t.transform.translation.y = msg.people[0].pos.y
    t.transform.translation.z = msg.people[0].pos.z
    q = tf_conversions.transformations.quaternion_from_euler(0, 0, math.pi/2)
    t.transform.rotation.x = q[0]
    t.transform.rotation.y = q[1]
    t.transform.rotation.z = q[2]
    t.transform.rotation.w = q[3]

    br.sendTransform(t)

    print(f"leggies found:{t.transform.translation.z}")
    
    goal.x = t.transform.rotation.x
    goal.y = t.transform.rotation.y

    theta = t.transform.rotation.z



def listener():
    global pub, goal, x, y, theta

    rospy.init_node('leggies_broadcaster')
    rospy.Subscriber('/people_tracker_measurements', PositionMeasurementArray, handle_leggies)
    rospy.Subscriber('/odom', Odometry, localRad)
    #rospy.Subscriber('/base_scan', LaserScan, avoid_follow)
    pub = rospy.Publisher("/cmd_vel" , Twist , queue_size=1)

    while not rospy.is_shutdown():

        inc_x = goal.x -x
        inc_y = goal.y -y

        angle_to_goal = atan2(inc_y, inc_x)

        if abs(angle_to_goal - theta) > 0.1:
            msg_twist.linear.x = 0.0
            msg_twist.angular.z = 0.3
        else:
            msg_twist.linear.x = 0.5
            msg_twist.angular.z = 0.0

        pub.publish(msg_twist)
    
    rospy.spin()



if __name__ == '__main__':
    listener()
