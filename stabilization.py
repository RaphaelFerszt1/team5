import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
stabilizers ={}

def register(cls):
    stabilizers[cls.__name__] = cls

# @register
# class OpticalFlowStabilization:
#     def __init__(self,key_point_kwargs:dict = None,optical_flow_kwargs:dict = None) -> None:
#         self.key_point_kwargs = key_point_kwargs if key_point_kwargs is not None else {} # max_corners: int = 300, quality_level: int =0.01, min_distance: int = 30, block_size: int=3
#         self.optical_flow_kwargs = optical_flow_kwargs if optical_flow_kwargs is not None else {}
#         self.previous_singel_channel_frame = None


#     def __call__(self, singel_channel_frame):

#         rotation_mat = self.get_rotation_mat(frame=singel_channel_frame)
#         if rotation_mat is not None:
#             rotated_frame = self.rotate_frame(singel_channel_frame,rotation_mat)
        
#         else:
#             rotated_frame = singel_channel_frame

#         return rotated_frame

#     def get_rotation_mat(self,frame):
#         # Assumes that the frame consists onlu of 1 channel i.e (w,h)

#         if self.previous_singel_channel_frame is None:
#             self.previous_singel_channel_frame = frame
#             return None
        

#         frame_key_points = cv.goodFeaturesToTrack(frame, **self.key_point_kwargs)
#         frame_key_points_previous_position,status,err = cv.calcOpticalFlowPyrLK(frame,self.previous_singel_channel_frame,frame_key_points, **self.optical_flow_kwargs)
#         assert frame_key_points_previous_position.shape ==frame_key_points.shape

#         # find the points where opticalflow sucsseded 
#         success_indices = np.where(status==1)[0]
#         frame_key_points, frame_key_points_previous_position = frame_key_points[success_indices],frame_key_points_previous_position[success_indices]
#         # Estimate the transition matrix from current frame to the previous one
#         rot_mat, mask = cv.findHomography(frame_key_points, frame_key_points_previous_position, cv.RANSAC,5.0)
#         # Update the previous gray frame to the next call.
#         self.previous_singel_channel_frame = frame
#         return rot_mat
    

#     @staticmethod
#     def rotate_frame(frame,rot_mat):
#         rotated_frame = cv.warpPerspective(frame, rot_mat, (frame.shape[1],frame.shape[0]))
#         return rotated_frame

@register
class OpticalFlowStabilization:
    def __init__(self,rotation_matrix_buffer_size=10,key_point_kwargs:dict = None,optical_flow_kwargs:dict = None) -> None:
        self.key_point_kwargs = key_point_kwargs if key_point_kwargs is not None else {} # max_corners: int = 300, quality_level: int =0.01, min_distance: int = 30, block_size: int=3
        self.optical_flow_kwargs = optical_flow_kwargs if optical_flow_kwargs is not None else {}
        self.previous_singel_channel_frame = None
        self.rotation_matrix_buffer = []
        self.rotation_matrix_buffer_size = rotation_matrix_buffer_size

    def __call__(self, singel_channel_frame):

        rotation_mat = self.get_rotation_mat(frame=singel_channel_frame)

        # Smooth the rotation matrix using a temporal filter.
        if rotation_mat is not None:
            self.rotation_matrix_buffer.append(rotation_mat)
            if len(self.rotation_matrix_buffer) > self.rotation_matrix_buffer_size:
                self.rotation_matrix_buffer.pop(0)
            rotation_mat = np.mean(self.rotation_matrix_buffer, axis=0)

        # Rotate the frame.
        if rotation_mat is not None:
            rotated_frame = self.rotate_frame(singel_channel_frame,rotation_mat)
        else:
            rotated_frame = singel_channel_frame

        return rotated_frame

    def get_rotation_mat(self,frame):
        # Assumes that the frame consists onlu of 1 channel i.e (w,h)

        if self.previous_singel_channel_frame is None:
            self.previous_singel_channel_frame = frame
            return None
        

        frame_key_points = cv.goodFeaturesToTrack(frame, **self.key_point_kwargs)
        frame_key_points_previous_position,status,err = cv.calcOpticalFlowPyrLK(frame,self.previous_singel_channel_frame,frame_key_points, **self.optical_flow_kwargs)
        assert frame_key_points_previous_position.shape ==frame_key_points.shape

        # Find the points where optical flow succeeded.
        success_indices = np.where(status==1)[0]
        frame_key_points, frame_key_points_previous_position = frame_key_points[success_indices],frame_key_points_previous_position[success_indices]

        # Estimate the homography.
        rot_mat, mask = cv.findHomography(frame_key_points, frame_key_points_previous_position, cv.RANSAC,10.0)

        # Update the previous gray frame to the next call.
        self.previous_singel_channel_frame = frame

        return rot_mat
    

    @staticmethod
    def rotate_frame(frame,rot_mat):
        rotated_frame = cv.warpPerspective(frame, rot_mat, (frame.shape[1],frame.shape[0]))
        return rotated_frame
