/**
 * COGNIVEX - Feature Extraction
 * 
 * Extracts 8 behavioral features from raw events:
 * 1. typing_speed - keys per second
 * 2. backspace_ratio - backspace presses / total keys
 * 3. avg_keystroke_interval - time between key presses
 * 4. keystroke_variance - variance in keystroke timing
 * 5. avg_mouse_speed - average pixels per second
 * 6. mouse_move_variance - variance in mouse speed
 * 7. scroll_frequency - scrolls per second
 * 8. idle_ratio - time without typing / total time
 */

class FeatureExtractor {
    /**
     * Extract 8 features from raw behavioral data
     */
    static extract(rawData) {
        const keyEvents = rawData.key_events || [];
        const mouseEvents = rawData.mouse_events || [];
        const scrollEvents = rawData.scroll_events || [];

        const features = {
            typing_speed: this.getTypingSpeed(keyEvents),
            backspace_ratio: this.getBackspaceRatio(keyEvents),
            avg_keystroke_interval: this.getKeystrokeInterval(keyEvents),
            keystroke_variance: this.getKeystrokeVariance(keyEvents),
            avg_mouse_speed: this.getMouseSpeed(mouseEvents),
            mouse_move_variance: this.getMouseVariance(mouseEvents),
            scroll_frequency: this.getScrollFrequency(scrollEvents),
            idle_ratio: this.getIdleRatio(keyEvents)
        };

        return features;
    }

    /**
     * Feature 1: Typing Speed (keys per second)
     */
    static getTypingSpeed(keyEvents) {
        if (keyEvents.length < 2) return 0;

        const keyups = keyEvents.filter(e => e.type === 'keyup');
        const duration = (keyEvents[keyEvents.length - 1].timestamp - keyEvents[0].timestamp) / 1000;

        if (duration === 0) return 0;
        return keyups.length / duration;
    }

    /**
     * Feature 2: Backspace Ratio
     */
    static getBackspaceRatio(keyEvents) {
        if (keyEvents.length === 0) return 0;

        const backspaces = keyEvents.filter(e => e.key === 'Backspace').length;
        return backspaces / keyEvents.length;
    }

    /**
     * Feature 3: Average Keystroke Interval (seconds)
     */
    static getKeystrokeInterval(keyEvents) {
        const keyups = keyEvents.filter(e => e.type === 'keyup');
        
        if (keyups.length < 2) return 0;

        let totalInterval = 0;
        for (let i = 0; i < keyups.length - 1; i++) {
            totalInterval += keyups[i + 1].timestamp - keyups[i].timestamp;
        }

        return (totalInterval / (keyups.length - 1)) / 1000; // Convert to seconds
    }

    /**
     * Feature 4: Keystroke Variance
     */
    static getKeystrokeVariance(keyEvents) {
        const keyups = keyEvents.filter(e => e.type === 'keyup');
        
        if (keyups.length < 2) return 0;

        const intervals = [];
        for (let i = 0; i < keyups.length - 1; i++) {
            intervals.push(keyups[i + 1].timestamp - keyups[i].timestamp);
        }

        const mean = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const variance = intervals.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / intervals.length;
        
        return Math.sqrt(variance) / 1000; // Standard deviation in seconds
    }

    /**
     * Feature 5: Average Mouse Speed (pixels per second)
     */
    static getMouseSpeed(mouseEvents) {
        if (mouseEvents.length < 2) return 0;

        let totalDistance = 0;
        for (let i = 0; i < mouseEvents.length - 1; i++) {
            const current = mouseEvents[i];
            const next = mouseEvents[i + 1];
            
            const distance = Math.sqrt(
                Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
            );
            totalDistance += distance;
        }

        const duration = (mouseEvents[mouseEvents.length - 1].timestamp - mouseEvents[0].timestamp) / 1000;
        
        if (duration === 0) return 0;
        return totalDistance / duration;
    }

    /**
     * Feature 6: Mouse Movement Variance
     */
    static getMouseVariance(mouseEvents) {
        if (mouseEvents.length < 2) return 0;

        const speeds = [];
        for (let i = 0; i < mouseEvents.length - 1; i++) {
            const current = mouseEvents[i];
            const next = mouseEvents[i + 1];
            
            const distance = Math.sqrt(
                Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
            );
            const timeDiff = (next.timestamp - current.timestamp) / 1000;
            
            if (timeDiff > 0) {
                speeds.push(distance / timeDiff);
            }
        }

        if (speeds.length === 0) return 0;

        const mean = speeds.reduce((a, b) => a + b, 0) / speeds.length;
        const variance = speeds.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / speeds.length;
        
        return Math.sqrt(variance);
    }

    /**
     * Feature 7: Scroll Frequency (scrolls per second)
     */
    static getScrollFrequency(scrollEvents) {
        if (scrollEvents.length < 2) return 0;

        const duration = (scrollEvents[scrollEvents.length - 1].timestamp - scrollEvents[0].timestamp) / 1000;
        
        if (duration === 0) return 0;
        return scrollEvents.length / duration;
    }

    /**
     * Feature 8: Idle Ratio (time without typing / total time)
     */
    static getIdleRatio(keyEvents) {
        const keyups = keyEvents.filter(e => e.type === 'keyup');
        
        if (keyups.length < 2) return 0;

        let activeTime = 0;
        for (let i = 0; i < keyups.length - 1; i++) {
            activeTime += keyups[i + 1].timestamp - keyups[i].timestamp;
        }

        const totalTime = keyups[keyups.length - 1].timestamp - keyups[0].timestamp;
        
        if (totalTime === 0) return 0;
        
        return 1 - (activeTime / totalTime);
    }

    /**
     * Aggregate features from multiple snapshots
     * (Used at session end)
     */
    static aggregateFeatures(snapshots) {
        if (snapshots.length === 0) {
            return this.getDefaultFeatures();
        }

        const allFeatures = snapshots.map(snapshot => {
            return this.extract(snapshot.raw_data || snapshot);
        });

        // Average all features
        const featureNames = Object.keys(allFeatures[0]);
        const aggregated = {};

        for (const featureName of featureNames) {
            const values = allFeatures.map(f => f[featureName]);
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            aggregated[featureName] = parseFloat(avg.toFixed(6));
        }

        return aggregated;
    }

    /**
     * Get default (zero) features
     */
    static getDefaultFeatures() {
        return {
            typing_speed: 0,
            backspace_ratio: 0,
            avg_keystroke_interval: 0,
            keystroke_variance: 0,
            avg_mouse_speed: 0,
            mouse_move_variance: 0,
            scroll_frequency: 0,
            idle_ratio: 0
        };
    }
}

// Make available globally
window.FeatureExtractor = FeatureExtractor;

console.log('✅ Feature Extractor loaded');