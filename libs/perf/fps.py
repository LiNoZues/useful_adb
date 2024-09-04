class FPS:
    def __init__(self,jank_threshold = 166,package_name = None,sdk_version = None):
        self._use_legacy_method = False
        self.jank_threshold = jank_threshold/1000.0   # 计算jank值的阈值，单位毫秒，默认10个时钟周期，166ms
        self.package_name = package_name
        self._sdk_version = sdk_version

    def _get_surfaceflinger_frame_data_by_gfx(self,period_time,frame_data):
        # https://www.cnblogs.com/zhengna/p/10032078.html
        """Returns collected SurfaceFlinger frame timing data.
        return:(16.6,[[t1,t2,t3],[t4,t5,t6]])
        Returns:
            A tuple containing:
            - The display's nominal refresh period in seconds.
            - A list of timestamps signifying frame presentation times in seconds.
            The return value may be (None, None) if there was no data collected (for
            example, if the app was closed before the collector thread has finished).
        """
        refresh_period = None
        timestamps = []
        nanoseconds_per_second = 1e9
        pending_fence_timestamp = (1 << 63) - 1
        
        # 每一帧花费的时间
        refresh_period = int(period_time)/nanoseconds_per_second
        if not len(frame_data):
            raise Exception('Unable to get surface flinger latency data')

        isHaveFoundWindow = False
        begin = False
        start_collect = False
        for line in frame_data:
            if "Window" in line and self.package_name in line:
                isHaveFoundWindow = True
            if not isHaveFoundWindow:
                continue
            if 'PROFILEDATA' in line and begin:
                # end
                break
            if 'PROFILEDATA' in line and not begin:
                # begin
                begin = True
            if 'Flags' in line:
                start_collect = True
            if start_collect:
                fields = line.split(',')
                if fields[0] !='0':
                    # 异常帧忽略
                    continue
                # 获取INTENDED_VSYNC VSYNC FRAME_COMPLETED时间 利用VSYNC计算fps jank
                timestamp = [int(fields[1]),int(fields[2]),int(fields[13])]
                if timestamp[1] == pending_fence_timestamp:
                    continue
                timestamp = [_timestamp / nanoseconds_per_second for _timestamp in timestamp]
                timestamps.append(timestamp)
            
            
        return refresh_period, timestamps
                
    def _get_surfaceflinger_frame_data_by_surface(self,frame_data):
        # https://testerhome.com/topics/1919
        # adb shell dumpsys SurfaceFlinger --latency <window name>
        # prints some information about the last 128 frames displayed in
        # that window.
        # The data returned looks like this:
        # 16954612
        # 7657467895508   7657482691352   7657493499756
        # 7657484466553   7657499645964   7657511077881
        # 7657500793457   7657516600576   7657527404785
        # (...)
        #
        # The first line is the refresh period (here 16.95 ms), it is followed
        # by 128 lines w/ 3 timestamps in nanosecond each:
        # A) when the app started to draw
        # B) the vsync immediately preceding SF submitting the frame to the h/w
        # C) timestamp immediately after SF submitted that frame to the h/w
        #
        # The difference between the 1st and 3rd timestamp is the frame-latency.
        # An interesting data is when the frame latency crosses a refresh period
        # boundary, this can be calculated this way:
        #
        # ceil((C - A) / refresh-period)
        #
        # (each time the number above changes, we have a "jank").
        # If this happens a lot during an animation, the animation appears
        # janky, even if it runs at 60 fps in average.
        #
        # We use the special "SurfaceView" window name because the statistics for
        # the activity's main window are not updated when the main web content is
        # composited into a SurfaceView.
        # frame_data =self.adb.surfaceflinger_latency_for_fps()
        if not len(frame_data):
            raise Exception('Unable to get surface flinger latency data')

        timestamps = []
        nanoseconds_per_second = 1e9
        refresh_period = int(frame_data[0]) / nanoseconds_per_second

        # If a fence associated with a frame is still pending when we query the
        # latency data, SurfaceFlinger gives the frame a timestamp of INT64_MAX.
        # Since we only care about completed frames, we will ignore any timestamps
        # with this value.
        pending_fence_timestamp = (1 << 63) - 1

        for line in frame_data[1:]:
            fields = line.split()
            if len(fields) != 3:
                continue
            timestamp = [int(fields[0]),int(fields[1]),int(fields[2])]
            if timestamp[1] == pending_fence_timestamp:
                continue
            timestamp = [_timestamp / nanoseconds_per_second for _timestamp in timestamp]
            timestamps.append(timestamp)

        return (refresh_period, timestamps)

    def _calculate_janky(self,timestamps):
        tempstamp = 0
        #统计丢帧卡顿
        jank = 0
        for timestamp in timestamps:
            if tempstamp == 0:
                tempstamp = timestamp[1]
                continue
            #绘制帧耗时
            costtime = timestamp[1] - tempstamp
            #耗时大于阈值10个时钟周期,用户能感受到卡顿感
            
            if costtime > 168/10000:
                print(costtime)
                jank = jank + 1
            tempstamp = timestamp[1]
        return jank

    def _calculate_results_new(self, timestamps):
        """Returns a list of SurfaceStatsCollector.Result.
        不少手机第一列  第三列 数字完全相同
        """
        frame_count = len(timestamps)
        if frame_count ==0:
            fps = 0
            jank = 0
        elif frame_count == 1:
            fps = 1
            jank = 0
        elif frame_count == 2 or frame_count ==3 or frame_count==4:
            seconds = timestamps[-1][1] - timestamps[0][1]
            if seconds > 0:
                fps = int(round((frame_count - 1) / seconds))
                jank = self._calculate_janky(timestamps)
            else:
                fps = 1
                jank = 0
        else:
            seconds = timestamps[-1][1] - timestamps[0][1]
            if seconds > 0:
                fps = int(round((frame_count - 1) / seconds))
                jank =self._calculate_jankey_new(timestamps)
            else:
                fps = 1
                jank = 0
        return fps,jank
    
    def _calculate_jankey_new(self,timestamps):

        '''同时满足两个条件计算为一次卡顿：
            ①Display FrameTime>前三帧平均耗时2倍。
            ②Display FrameTime>两帧电影帧耗时 (1000ms/24*2≈83.33ms)。
            '''

        twofilmstamp = 83.3 / 1000.0
        tempstamp = 0
        # 统计丢帧卡顿
        jank = 0
        for index,timestamp in enumerate(timestamps):
            #前面四帧按超过166ms计算为卡顿
            if (index == 0) or (index == 1) or (index == 2) or (index == 3):
                if tempstamp == 0:
                    tempstamp = timestamp[1]
                    continue
                # 绘制帧耗时
                costtime = timestamp[1] - tempstamp
                # 耗时大于阈值10个时钟周期,用户能感受到卡顿感
                if costtime > self.jank_threshold:
                    jank = jank + 1
                tempstamp = timestamp[1]
            elif index > 3:
                currentstamp = timestamps[index][1]
                lastonestamp = timestamps[index - 1][1]
                lasttwostamp = timestamps[index - 2][1]
                lastthreestamp = timestamps[index - 3][1]
                lastfourstamp = timestamps[index - 4][1]
                tempframetime = ((lastthreestamp - lastfourstamp) + (lasttwostamp - lastthreestamp) + (
                        lastonestamp - lasttwostamp)) / 3 * 2
                currentframetime = currentstamp - lastonestamp
                if (currentframetime > tempframetime) and (currentframetime > twofilmstamp):
                    jank = jank + 1
        return jank

    def get_fps(self,frame_data,period_time=None):
        if self._sdk_version >= 26:
            _, timestamps = self._get_surfaceflinger_frame_data_by_gfx(period_time,frame_data)
        else:
            _, timestamps = self._get_surfaceflinger_frame_data_by_surface(frame_data)
        _fps,_jank = self._calculate_results_new(timestamps)
        return _fps,_jank
