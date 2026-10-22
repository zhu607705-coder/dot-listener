package dev.dotlistener

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.io.File
import java.io.FileOutputStream
import java.security.KeyStore
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.CipherOutputStream
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

/** DL01 | 12-byte IV | AES-GCM ciphertext+tag. Plaintext: PCM16LE, mono, 16 kHz.
 * .part files have not been committed. Never pass them to ASR without recovery.
 */
class EncryptedSegments(private val directory: File) {
    private val alias = "dot-listener-audio-v1"
    private var stream: CipherOutputStream? = null
    private var part: File? = null
    private var bytes = 0
    init { directory.mkdirs() }
    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getKey(alias, null) as? SecretKey)?.let { return it }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build())
        return generator.generateKey()
    }
    private fun open() {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        require(cipher.iv.size == 12)
        cipher.updateAAD("DL01|16000|1|s16le".toByteArray(Charsets.UTF_8))
        val f = File(directory, "${System.currentTimeMillis()}-${UUID.randomUUID()}.pcm.enc.part")
        val output = FileOutputStream(f)
        output.write("DL01".toByteArray(Charsets.US_ASCII)); output.write(cipher.iv)
        part = f; stream = CipherOutputStream(output, cipher); bytes = 0
    }
    @Synchronized fun write(buffer: ByteArray, count: Int) {
        require(count in 0..buffer.size)
        if (stream == null) open()
        stream!!.write(buffer, 0, count); bytes += count
        if (bytes >= 16000 * 2 * 30) close()
    }
    @Synchronized fun close() {
        val current = stream ?: return
        val file = part!!
        try { current.close() } finally { stream = null; part = null }
        check(file.renameTo(File(directory, file.name.removeSuffix(".part")))) { "Segment commit failed" }
    }
}
