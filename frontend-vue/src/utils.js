function getNextCronExecution(cronExpression) {
  // Handle special strings
  const specialExpressions = {
    '@yearly': '0 0 1 1 *',
    '@annually': '0 0 1 1 *',
    '@monthly': '0 0 1 * *',
    '@weekly': '0 0 * * 0',
    '@daily': '0 0 * * *',
    '@midnight': '0 0 * * *',
    '@hourly': '0 * * * *'
  };
  
  if (specialExpressions[cronExpression.toLowerCase()]) {
    cronExpression = specialExpressions[cronExpression.toLowerCase()];
  }
  
  const parts = cronExpression.trim().split(/\s+/);
  
  if (parts.length !== 5) {
    throw new Error('Invalid cron expression. Expected 5 parts: minute hour day month dayOfWeek');
  }
  
  const [minutePart, hourPart, dayPart, monthPart, dayOfWeekPart] = parts;
  
  // Helper function to get days in a month
  function getDaysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
  }
  
  // Helper function to check if year is leap year
  function isLeapYear(year) {
    return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
  }
  
  // Helper function to get the nth weekday of a month
  function getNthWeekdayOfMonth(year, month, weekday, nth) {
    const firstDay = new Date(year, month - 1, 1);
    const firstWeekday = firstDay.getDay();
    
    // Calculate the first occurrence of the target weekday
    let firstOccurrence = 1 + (weekday - firstWeekday + 7) % 7;
    
    // Calculate the nth occurrence
    let nthOccurrence = firstOccurrence + (nth - 1) * 7;
    
    // Check if it exists in this month
    if (nthOccurrence <= getDaysInMonth(year, month)) {
      return nthOccurrence;
    }
    
    return null;
  }
  
  // Helper function to find nearest weekday to a given date
  function getNearestWeekday(year, month, targetDay) {
    const daysInMonth = getDaysInMonth(year, month);
    
    // Ensure target day is within month bounds
    if (targetDay > daysInMonth) {
      targetDay = daysInMonth;
    }
    
    const date = new Date(year, month - 1, targetDay);
    const dayOfWeek = date.getDay();
    
    if (dayOfWeek === 0) { // Sunday
      // Try Monday (next day)
      if (targetDay + 1 <= daysInMonth) {
        return targetDay + 1;
      }
      // Try Friday (previous day)
      if (targetDay - 2 >= 1) {
        return targetDay - 2;
      }
      return targetDay + 1; // Even if it goes to next month
    } else if (dayOfWeek === 6) { // Saturday
      // Try Friday (previous day)
      if (targetDay - 1 >= 1) {
        return targetDay - 1;
      }
      // Try Monday (next day)
      if (targetDay + 2 <= daysInMonth) {
        return targetDay + 2;
      }
      return targetDay - 1; // Even if it goes to previous month
    }
    
    return targetDay; // Already a weekday
  }
  
  // Advanced cron field parser
  function parseCronField(field, min, max, year = null, month = null) {
    if (field === '*' || field === '?') {
      return Array.from({ length: max - min + 1 }, (_, i) => i + min);
    }
    
    // Handle last day of month (L)
    if (field === 'L' && year && month) {
      return [getDaysInMonth(year, month)];
    }
    
    // Handle last specific weekday (e.g., 5L for last Friday)
    if (field.endsWith('L') && year && month) {
      const weekday = parseInt(field.slice(0, -1));
      const daysInMonth = getDaysInMonth(year, month);
      
      // Find the last occurrence of this weekday
      for (let day = daysInMonth; day >= 1; day--) {
        const date = new Date(year, month - 1, day);
        if (date.getDay() === weekday) {
          return [day];
        }
      }
      return [];
    }
    
    // Handle weekday nearest to date (W)
    if (field.endsWith('W') && year && month) {
      const targetDay = parseInt(field.slice(0, -1));
      return [getNearestWeekday(year, month, targetDay)];
    }
    
    // Handle nth weekday (e.g., 1#3 for third Monday)
    if (field.includes('#')) {
      const [weekday, nth] = field.split('#').map(Number);
      if (year && month) {
        const nthDay = getNthWeekdayOfMonth(year, month, weekday, nth);
        return nthDay ? [nthDay] : [];
      }
      return []; // Can't resolve without year/month
    }
    
    // Handle comma-separated values
    if (field.includes(',')) {
      return field.split(',').flatMap(part => parseCronField(part.trim(), min, max, year, month));
    }
    
    // Handle step values
    if (field.includes('/')) {
      const [range, step] = field.split('/');
      const stepNum = parseInt(step);
      
      let baseRange;
      if (range === '*') {
        baseRange = Array.from({ length: max - min + 1 }, (_, i) => i + min);
      } else {
        baseRange = parseCronField(range, min, max, year, month);
      }
      
      if (range === '*') {
        return baseRange.filter(val => (val - min) % stepNum === 0);
      } else {
        return baseRange.filter((_, index) => index % stepNum === 0);
      }
    }
    
    // Handle ranges
    if (field.includes('-')) {
      const [start, end] = field.split('-').map(Number);
      return Array.from({ length: end - start + 1 }, (_, i) => i + start);
    }
    
    // Single numeric value
    const num = parseInt(field);
    return [num];
  }
  
  // Start from current time + 1 minute
  const now = new Date();
  let nextTime = new Date(now.getTime() + 60000);
  nextTime.setSeconds(0);
  nextTime.setMilliseconds(0);
  
  // Find next valid execution time
  for (let attempt = 0; attempt < 366 * 24 * 60 * 2; attempt++) { // 2 years max
    const year = nextTime.getFullYear();
    const month = nextTime.getMonth() + 1;
    const day = nextTime.getDate();
    const hour = nextTime.getHours();
    const minute = nextTime.getMinutes();
    const dayOfWeek = nextTime.getDay();
    
    // Parse fields with current date context for advanced features
    const minutes = parseCronField(minutePart, 0, 59);
    const hours = parseCronField(hourPart, 0, 23);
    const days = parseCronField(dayPart, 1, 31, year, month);
    const months = parseCronField(monthPart, 1, 12);
    const daysOfWeek = dayOfWeekPart === '*' || dayOfWeekPart === '?' ? 
      null : parseCronField(dayOfWeekPart, 0, 6, year, month);
    
    // Check matches
    const monthMatch = months.includes(month);
    const hourMatch = hours.includes(hour);
    const minuteMatch = minutes.includes(minute);
    
    // Handle day/dayOfWeek logic properly
    let dayMatch = false;
    
    if (dayPart === '*' && (dayOfWeekPart === '*' || dayOfWeekPart === '?')) {
      // Both wildcards - any day is valid
      dayMatch = true;
    } else if (dayPart === '*' || dayPart === '?') {
      // Only day is wildcard - use dayOfWeek
      dayMatch = daysOfWeek && daysOfWeek.includes(dayOfWeek);
    } else if (dayOfWeekPart === '*' || dayOfWeekPart === '?') {
      // Only dayOfWeek is wildcard - use day
      dayMatch = days.includes(day);
    } else {
      // Both specified - either can match (OR condition)
      dayMatch = days.includes(day) || (daysOfWeek && daysOfWeek.includes(dayOfWeek));
    }
    
    // Validate day exists in month (handle Feb 29, etc.)
    const daysInCurrentMonth = getDaysInMonth(year, month);
    const validDay = day <= daysInCurrentMonth;
    
    if (monthMatch && dayMatch && hourMatch && minuteMatch && validDay) {
      // Format output as DD.MM.YYYY, HH:MM:SS
      const formattedDate = String(day).padStart(2, '0') + '.' + 
                           String(month).padStart(2, '0') + '.' + 
                           year;
      const formattedTime = String(hour).padStart(2, '0') + ':' + 
                           String(minute).padStart(2, '0') + ':00';
      
      return formattedDate + ', ' + formattedTime;
    }
    
    // Increment by 1 minute
    nextTime.setMinutes(nextTime.getMinutes() + 1);
  }
  
  throw new Error('Could not find next execution time within reasonable range (2 years)');
}

export { getNextCronExecution };