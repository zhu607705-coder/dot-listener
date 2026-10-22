package dev.dotlistener

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.*
import android.widget.*

class MainActivity : Activity() {
    private val prefs by lazy { getSharedPreferences("listener", MODE_PRIVATE) }
    private lateinit var status: TextView
    private lateinit var consent: CheckBox
    private val handler = Handler(Looper.getMainLooper())
    private val refresh = object : Runnable {
        override fun run() {
            val last = prefs.getLong("lastAudioReadMs", 0)
            val age = if (last == 0L) "尚无读取" else "最后音频读取距今 ${(System.currentTimeMillis()-last)/1000} 秒"
            status.text = "${prefs.getString("state", "IDLE")}\n$age\nASR 未接入 · dot 未连接 · GT 6 Pro 未验证"
            handler.postDelayed(this, 1000)
        }
    }
    private fun minute(value: String): Int {
        val parts = value.split(":"); require(parts.size == 2)
        val h = parts[0].toInt(); val m = parts[1].toInt(); require(h in 0..23 && m in 0..59)
        return h*60+m
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(28,36,28,28) }
        val scroll = ScrollView(this); scroll.addView(layout); setContentView(scroll)
        fun label(text: String) = TextView(this).also { it.text=text; it.textSize=17f; layout.addView(it) }
        label("Dot Listener / 采集验证版").textSize=27f
        label("仅保存本机加密音频；没有语音转写或自动上传。请明确告知同场人员，随时可停止。")
        status=label("")
        consent=CheckBox(this).apply { text="我已完成必要告知，允许本次录音" };layout.addView(consent)
        label("睡眠时段（手机本地时区；下面仅为示例，请修改）")
        val start=EditText(this).apply {setText(java.lang.String.format(java.util.Locale.ROOT,"%02d:%02d",prefs.getInt("sleepStart",0)/60,prefs.getInt("sleepStart",0)%60));hint="睡眠开始 HH:mm"};layout.addView(start)
        val end=EditText(this).apply {setText(java.lang.String.format(java.util.Locale.ROOT,"%02d:%02d",prefs.getInt("sleepEnd",480)/60,prefs.getInt("sleepEnd",480)%60));hint="睡眠结束 HH:mm"};layout.addView(end)
        val begin=Button(this).apply {text="开始本次录音"};layout.addView(begin)
        begin.setOnClickListener {
            try {
                require(consent.isChecked) { "请先确认录音告知" }
                val window=SleepWindow(minute(start.text.toString()), minute(end.text.toString()))
                prefs.edit().putInt("sleepStart",window.start).putInt("sleepEnd",window.end).putBoolean("consent",true).apply()
                val needed=mutableListOf(Manifest.permission.RECORD_AUDIO)
                if (Build.VERSION.SDK_INT>=33) needed.add(Manifest.permission.POST_NOTIFICATIONS)
                val missing=needed.filter {checkSelfPermission(it)!=PackageManager.PERMISSION_GRANTED}
                if (missing.isNotEmpty()) {
                    requestPermissions(missing.toTypedArray(),1)
                    Toast.makeText(this,"授权后请再点一次开始",Toast.LENGTH_LONG).show()
                } else startForegroundService(Intent(this,RecordingService::class.java).setAction("START_FROM_VISIBLE_UI"))
            } catch (e: Exception) { Toast.makeText(this,e.message?:"请检查设置",Toast.LENGTH_LONG).show() }
        }
        val stop=Button(this).apply {text="暂停 / 我去睡觉了"};layout.addView(stop)
        stop.setOnClickListener {
            prefs.edit().putString("state","PAUSED: user request").apply()
            stopService(Intent(this,RecordingService::class.java))
        }
        label("睡眠开始时自动停止；次日需打开应用再点开始。程序被终止后不会偷偷重启麦克风。")
    }
    override fun onResume() { super.onResume();handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh);super.onPause() }
}
