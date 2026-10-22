package dev.dotlistener

import android.Manifest
import android.app.*
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.*
import android.os.*
import java.io.File
import java.time.ZonedDateTime
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** Experimental capture source. No ASR, network sync or Huawei APIs are included. */
class RecordingService : Service() {
    private val running = AtomicBoolean(false)
    private val worker = Executors.newSingleThreadExecutor()
    private val main = Handler(Looper.getMainLooper())
    private val captureLock = Any()
    @Volatile private var recorder: AudioRecord? = null
    private val prefs by lazy { getSharedPreferences("listener", MODE_PRIVATE) }
    private val callback = object : AudioManager.AudioRecordingCallback() {
        override fun onRecordingConfigChanged(configs: MutableList<AudioRecordingConfiguration>) {
            val id = recorder?.audioSessionId ?: return
            if (configs.any { it.clientAudioSessionId == id && it.isClientSilenced }) {
                prefs.edit().putString("state", "INTERRUPTED: microphone silenced").apply()
                stopSelf() // fail visible; never manufacture an all-day coverage claim
            }
        }
    }
    override fun onBind(intent: Intent?) = null
    override fun onCreate() {
        super.onCreate()
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel("capture", "日间录音状态", NotificationManager.IMPORTANCE_LOW))
        getSystemService(AudioManager::class.java).registerAudioRecordingCallback(callback, main)
    }
    private fun sleeping(): Boolean {
        val start = prefs.getInt("sleepStart", -1); val end = prefs.getInt("sleepEnd", -1)
        if (start < 0 || end < 0) return false
        val now = ZonedDateTime.now()
        return SleepWindow(start, end).contains(now.hour * 60 + now.minute)
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action != "START_FROM_VISIBLE_UI" ||
            !prefs.getBoolean("consent", false) ||
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED || sleeping()) {
            prefs.edit().putString("state", "STOPPED: consent/permission/sleep gate").apply()
            stopSelf(); return START_NOT_STICKY
        }
        if (!running.compareAndSet(false, true)) return START_NOT_STICKY
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val notification = Notification.Builder(this, "capture")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentTitle("Dot Listener 正在录音")
            .setContentText("原始音频仅保存在手机。打开应用可停止。转写尚未接入。")
            .setContentIntent(open).setOngoing(true).build()
        startForeground(1, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
        worker.execute { captureLoop(startId) }
        return START_NOT_STICKY
    }
    @Suppress("MissingPermission")
    private fun captureLoop(startId: Int) {
        val sink = EncryptedSegments(File(filesDir, "recordings"))
        var local: AudioRecord? = null
        try {
            val minimum = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
            check(minimum > 0)
            local = AudioRecord(MediaRecorder.AudioSource.MIC, 16000, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, maxOf(minimum, 8192))
            check(local.state == AudioRecord.STATE_INITIALIZED)
            synchronized(captureLock) {
                // Serialize start with onDestroy: a queued worker cannot restart a stopped service.
                if (!running.get()) return
                recorder = local
                local.startRecording()
                prefs.edit().putString("state", "RECORDING").apply()
            }
            val buffer = ByteArray(maxOf(minimum, 8192))
            while (running.get()) {
                if (sleeping()) { prefs.edit().putString("state", "SLEEP: microphone released").apply(); break }
                check(File(filesDir.absolutePath).usableSpace > 256L * 1024 * 1024) { "Low storage" }
                val count = readWhileRunning(running::get) {
                    local.read(buffer, 0, buffer.size, AudioRecord.READ_BLOCKING)
                } ?: break
                sink.write(buffer, count)
                prefs.edit().putLong("lastAudioReadMs", System.currentTimeMillis()).apply()
            }
        } catch (e: Exception) {
            if (running.get()) prefs.edit().putString("state", "ERROR: ${e.javaClass.simpleName}").apply()
        } finally {
            synchronized(captureLock) {
                running.set(false)
                runCatching { local?.stop() }; local?.release(); recorder = null
            }
            runCatching { sink.close() }.onFailure { prefs.edit().putString("state", "ERROR: incomplete segment").apply() }
            main.post { stopSelf(startId) }
        }
    }
    override fun onDestroy() {
        synchronized(captureLock) {
            running.set(false)
            runCatching { recorder?.stop() }
        }
        getSystemService(AudioManager::class.java).unregisterAudioRecordingCallback(callback)
        stopForeground(STOP_FOREGROUND_REMOVE)
        worker.shutdown()
        super.onDestroy()
    }
}
