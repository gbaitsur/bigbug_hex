#! /usr/bin/env python

# interface between bb_kinematics and dynamixel servos


# subscribes to /bb_hex/servo_targets topic for servo target angles (bb_msgs.msg.ServoTargets message)


# publishes voltage to /bb_hex/voltage topic (standard Float32 message)

# publishes current servo angles and loads to /bb_hex/servo_current topic (bb_msgs.msg.ServoCurrent message)


import rospy


def run():
    while not rospy.is_shutdown():
        pass


if __name__ == '__main__':
    rospy.init_node('bb_dynamixel', anonymous=True)
    try:
        run()
    except rospy.ROSInterruptException:
        pass