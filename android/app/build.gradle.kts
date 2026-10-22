plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "dev.dotlistener"
    compileSdk = 35
    defaultConfig {
        applicationId = "dev.dotlistener"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-scaffold"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
